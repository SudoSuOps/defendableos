"""Tests for the platform_admin creation script · validation paths only.

We can't fully test the DB-write path without a live database (the
existing test suite is pure-Python). What we CAN test is the validation
logic that prevents bad usage.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest


# Add the scripts dir to sys.path so we can import the bootstrap module
# This test file is at services/api/app/tests/ · scripts/ is at services/api/scripts/
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


def test_email_regex_accepts_valid_email():
    from create_platform_admin import EMAIL_RE
    assert EMAIL_RE.match("founder@defendableos.example")
    assert EMAIL_RE.match("admin@x.io")


def test_email_regex_rejects_invalid():
    from create_platform_admin import EMAIL_RE
    assert not EMAIL_RE.match("nope")
    assert not EMAIL_RE.match("nope@")
    assert not EMAIL_RE.match("@nope")
    assert not EMAIL_RE.match("nope @ space.com")
    assert not EMAIL_RE.match("a@b")  # no TLD


def test_min_password_length_enforced():
    from create_platform_admin import MIN_PASSWORD_LEN
    assert MIN_PASSWORD_LEN >= 16


def test_script_refuses_short_password(monkeypatch):
    """The _prompt_password function exits when password too short."""
    from create_platform_admin import _prompt_password
    monkeypatch.setattr("create_platform_admin.getpass.getpass",
                        lambda prompt: "short")
    with pytest.raises(SystemExit) as exc:
        _prompt_password()
    assert "too short" in str(exc.value)


def test_script_refuses_mismatched_passwords(monkeypatch):
    from create_platform_admin import _prompt_password
    responses = iter([
        "a-really-long-password-1234",
        "different-password-also-long",
    ])
    monkeypatch.setattr("create_platform_admin.getpass.getpass",
                        lambda prompt: next(responses))
    with pytest.raises(SystemExit) as exc:
        _prompt_password()
    assert "do not match" in str(exc.value)


def test_script_accepts_valid_password(monkeypatch):
    from create_platform_admin import _prompt_password
    valid_pw = "a-perfectly-fine-long-password-2026"
    monkeypatch.setattr("create_platform_admin.getpass.getpass",
                        lambda prompt: valid_pw)
    result = _prompt_password()
    assert result == valid_pw


def test_script_refuses_invalid_email(monkeypatch):
    from create_platform_admin import _prompt_email
    monkeypatch.setattr("builtins.input", lambda prompt: "not-an-email")
    with pytest.raises(SystemExit) as exc:
        _prompt_email()
    assert "valid email" in str(exc.value)


def test_script_refuses_empty_name(monkeypatch):
    from create_platform_admin import _prompt_name
    monkeypatch.setattr("builtins.input", lambda prompt: "   ")
    with pytest.raises(SystemExit) as exc:
        _prompt_name()
    assert "required" in str(exc.value)


def test_script_truncates_long_name(monkeypatch):
    from create_platform_admin import _prompt_name
    long_name = "x" * 500
    monkeypatch.setattr("builtins.input", lambda prompt: long_name)
    result = _prompt_name()
    assert len(result) <= 255


def test_script_module_does_not_log_passwords():
    """Source-grep: the script must NOT contain any logging of pw / password."""
    src = (SCRIPTS_DIR / "create_platform_admin.py").read_text()
    # Allow the variable name but not any print/log/echo of its value
    forbidden_patterns = (
        "print(pw",  # print(pw) or print(pw1) or print(pw2)
        "print(pwd",
        'f"{pw',
        "f'{pw",
    )
    for pat in forbidden_patterns:
        assert pat not in src, f"forbidden pw-print pattern in script: {pat!r}"


def test_script_uses_getpass_not_input_for_password():
    """The script reads passwords via getpass.getpass · NEVER via input()."""
    src = (SCRIPTS_DIR / "create_platform_admin.py").read_text()
    # _prompt_password must use getpass.getpass
    assert "getpass.getpass" in src
    # The password-prompting function must NOT use plain input()
    # (we use input() for email + name only · those are non-secret)
    lines = src.split("\n")
    in_pw_fn = False
    for line in lines:
        if "def _prompt_password" in line:
            in_pw_fn = True
            continue
        if in_pw_fn and line.startswith("def "):
            break
        if in_pw_fn and "input(" in line:
            raise AssertionError(
                "_prompt_password contains a plain input() call · should be getpass.getpass"
            )
