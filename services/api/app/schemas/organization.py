from __future__ import annotations

import uuid

from pydantic import BaseModel


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    ens_label: str | None
    ens_name: str | None
    ens_status: str

    model_config = {"from_attributes": True}
