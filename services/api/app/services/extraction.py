"""Lightweight text extraction for uploaded evidence (PDF / text / json / csv).

Image evidence is preserved as an object but not OCR'd in MVP. Extracted text
is private — it lives only in the organization's scope and is used to power
private evidence search.
"""
from __future__ import annotations

import csv
import io
import json
import uuid

from sqlalchemy.orm import Session

from app.models.evidence import (
    EvidenceChunk,
    EvidenceItem,
    ExtractedDocument,
    IngestionStatus,
)


def _chunk_text(text: str, target_chars: int = 1200) -> list[str]:
    if not text:
        return []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buffer = ""
    for p in paragraphs:
        if len(buffer) + len(p) + 2 <= target_chars:
            buffer = (buffer + "\n\n" + p).strip()
        else:
            if buffer:
                chunks.append(buffer)
            buffer = p
    if buffer:
        chunks.append(buffer)
    return chunks


def _extract_pdf(data: bytes) -> str:
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=data, filetype="pdf")
        return "\n\n".join(page.get_text("text") for page in doc)
    except Exception:
        return ""


def _extract_csv(data: bytes) -> str:
    try:
        text = data.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        return "\n".join(", ".join(row) for row in rows)
    except Exception:
        return ""


def _extract_json(data: bytes) -> str:
    try:
        obj = json.loads(data.decode("utf-8", errors="replace"))
        return json.dumps(obj, indent=2, sort_keys=True)
    except Exception:
        return data.decode("utf-8", errors="replace")


def _extract_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


EXTRACTORS = {
    "application/pdf": _extract_pdf,
    "text/csv": _extract_csv,
    "application/csv": _extract_csv,
    "application/json": _extract_json,
    "text/plain": _extract_text,
    "text/markdown": _extract_text,
}


def extract_evidence(
    db: Session,
    evidence: EvidenceItem,
    file_bytes: bytes,
) -> ExtractedDocument:
    content_type = (evidence.content_type or "").lower()
    extractor = EXTRACTORS.get(content_type, _extract_text)
    text = extractor(file_bytes) if file_bytes else ""

    chunks = _chunk_text(text)
    extracted = ExtractedDocument(
        id=uuid.uuid4(),
        evidence_item_id=evidence.id,
        extraction_status="DONE" if text else "EMPTY",
        extracted_text_private=text,
        chunk_count=len(chunks),
        metadata_json={"content_type": content_type},
    )
    db.add(extracted)
    for idx, chunk in enumerate(chunks):
        db.add(
            EvidenceChunk(
                id=uuid.uuid4(),
                evidence_item_id=evidence.id,
                organization_id=evidence.organization_id,
                asset_id=evidence.asset_id,
                chunk_index=idx,
                content=chunk,
                citation_locator=f"chunk {idx + 1}",
            )
        )
    evidence.ingestion_status = IngestionStatus.INDEXED if chunks else IngestionStatus.UPLOADED
    db.flush()
    return extracted


def private_search(
    db: Session,
    organization_id,
    asset_id,
    query: str,
    limit: int = 8,
) -> list[dict]:
    """Lexical search across the org+asset-scoped chunk table.

    MVP: case-insensitive substring match · simple, secure, predictable. A
    pgvector adapter can replace the body of this function later without
    changing the call sites.
    """
    if not query.strip():
        return []
    like = f"%{query.lower()}%"
    rows = (
        db.query(EvidenceChunk, EvidenceItem)
        .join(EvidenceItem, EvidenceItem.id == EvidenceChunk.evidence_item_id)
        .filter(
            EvidenceChunk.organization_id == organization_id,
            EvidenceChunk.asset_id == asset_id,
        )
        .filter(EvidenceChunk.content.ilike(like))
        .limit(limit)
        .all()
    )
    results = []
    for chunk, item in rows:
        excerpt = chunk.content
        if len(excerpt) > 400:
            excerpt = excerpt[:400] + "…"
        results.append(
            {
                "evidence_item_id": str(item.id),
                "filename": item.filename,
                "evidence_type": item.evidence_type.value,
                "locator": chunk.citation_locator,
                "excerpt": excerpt,
                "sha256": item.sha256_hash,
            }
        )
    return results
