"""Backend abstraction for narrative generation.

Three implementations:
- DeterministicBackend: template-based, always available, always passes
  validation. The production default on machines without a suitable GPU.
- MedGemmaBackend: local MedGemma inference, used when its weights and
  dependencies are installed.
- RemoteBackend: delegates to a separate model tier, sending de-identified
  values only. This is what lets the GPU run somewhere cheap without
  handling PHI.
- NimBackend: the same delegation against an NVIDIA NIM / TensorRT-LLM
  endpoint, which is how the model is served on a GPU in production.

All three produce untrusted output that goes through identical validation.

Backend selection never triggers a download or a network call.
"""

from __future__ import annotations

from typing import List, Protocol

from plainmed.config import AppConfig
from plainmed.schemas import NarrativeItem, ReportDocument


class ModelUnavailableError(RuntimeError):
    """The requested backend cannot run on this machine."""


class ModelOutputError(RuntimeError):
    """The backend produced output that could not be parsed."""


class ModelBackend(Protocol):
    name: str

    def generate(self, doc: ReportDocument) -> List[NarrativeItem]: ...


def get_backend(config: AppConfig) -> "ModelBackend":
    from plainmed.llm.deterministic import DeterministicBackend

    if config.backend == "deterministic":
        return DeterministicBackend()

    if config.backend == "nim":
        from plainmed.llm.nim import NimBackend

        return NimBackend(config)

    if config.backend == "remote":
        from plainmed.llm.remote import RemoteBackend

        return RemoteBackend(config)

    if config.backend in ("medgemma", "auto"):
        try:
            from plainmed.llm.medgemma import MedGemmaBackend

            return MedGemmaBackend(config)
        except ModelUnavailableError:
            if config.backend == "medgemma":
                raise
            return DeterministicBackend()

    raise ValueError(f"Unknown backend: {config.backend!r}")
