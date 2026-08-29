from __future__ import annotations

import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SAMPLES_DIR = ROOT / "samples"


@pytest.fixture
def no_network(monkeypatch):
    """Fail the test if anything in the pipeline tries to open a socket."""

    def _blocked(*args, **kwargs):
        raise AssertionError("A network call was attempted in offline mode.")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)


@pytest.fixture
def sample_texts() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(SAMPLES_DIR.glob("*.txt"))
    }
