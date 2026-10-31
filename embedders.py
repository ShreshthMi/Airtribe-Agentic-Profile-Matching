"""
Embedding providers for Round 1, beyond Milestone 2's local HuggingFace model.

Milestone 2 creates its embedder in two places, resume_rag.build_index() and
job_matcher.JobMatcher(), both by calling `Embedder(model_name)`, and it records the
model name in the index. install() points both at the Embedder below, which reads a
provider from that name:

  sentence-transformers/all-MiniLM-L6-v2   Milestone 2's model, the default, unchanged
  ollama:nomic-embed-text                  a local Ollama server; no key needed
  voyage:voyage-3.5                        Voyage AI; needs VOYAGE_API_KEY
  openai:text-embedding-3-small            OpenAI; needs OPENAI_API_KEY

Because the name is stored in the index, searching an index always uses the model it was
built with, and the vendored Milestone 2 files are not edited. Build an index with
scripts/build_index.py.
"""
from __future__ import annotations

import contextlib
import json
import math
import os
import urllib.error
import urllib.request

PROVIDERS = ("huggingface", "ollama", "voyage", "openai")
DEFAULT_MODELS = {"huggingface": "sentence-transformers/all-MiniLM-L6-v2", "ollama": "nomic-embed-text",
                  "voyage": "voyage-3.5", "openai": "text-embedding-3-small"}
CALIBRATION_FILE = "calibration.json"
BATCH_SIZE = 64
TIMEOUT_SECONDS = 120
LOW_PERCENTILE, HIGH_PERCENTILE = 0.10, 0.95

_original_embedder = None   # Milestone 2's own class, kept for HuggingFace models
_role = "query"             # "document" while an index is being built


class EmbeddingError(Exception):
    """An embedding provider could not be reached, refused the request, or is not set up."""


# --------------------------------------------------------------------------- #
# Choosing a provider
# --------------------------------------------------------------------------- #
def model_spec(provider: str, model: str | None = None) -> str:
    """The model name stored in an index: 'voyage:voyage-3.5', or Milestone 2's plain name."""
    if provider not in PROVIDERS:
        raise EmbeddingError(f"Unknown embedding provider {provider!r}; choose one of {', '.join(PROVIDERS)}.")
    model = model or DEFAULT_MODELS[provider]
    return model if provider == "huggingface" else f"{provider}:{model}"


def parse_spec(spec: str) -> tuple[str, str]:
    """('voyage', 'voyage-3.5') from 'voyage:voyage-3.5'; any other name is a HuggingFace model."""
    provider, separator, model = spec.partition(":")
    if separator and provider in PROVIDERS and provider != "huggingface":
        return provider, model
    return "huggingface", spec


class Embedder:
    """Drop-in for Milestone 2's Embedder: the same constructor and embed(), more providers."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        provider, model = parse_spec(model_name)
        if provider == "huggingface":
            self._client = _original_embedder(model)
            self.backend = self._client.backend
        else:
            self._client = CLIENTS[provider](model)
            self.backend = provider

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._client.embed(texts)


def install(*modules) -> None:
    """Make each module's `Embedder` the one above. Safe to call more than once."""
    global _original_embedder
    for module in modules:
        if module.Embedder is not Embedder:
            _original_embedder = _original_embedder or module.Embedder
            module.Embedder = Embedder


@contextlib.contextmanager
def documents():
    """Embed text as documents rather than search queries while inside this block.

    Voyage and nomic-embed-text embed a query and a document differently, and retrieve
    better when told which is which. Milestone 2's embed() has no such argument, so the
    index builder wraps itself in this block instead.
    """
    global _role
    previous, _role = _role, "document"
    try:
        yield
    finally:
        _role = previous


# --------------------------------------------------------------------------- #
# Hosted and local providers
# --------------------------------------------------------------------------- #
class _Client:
    def __init__(self, model: str):
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for start in range(0, len(texts), BATCH_SIZE):
            vectors += self._embed_batch(texts[start:start + BATCH_SIZE])
        return [_unit(v) for v in vectors]  # cosine space, like Milestone 2's vectors

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class OllamaClient(_Client):
    # Task prefixes the model was trained with; other models take the text as it is.
    PREFIXES = {"nomic-embed-text": {"document": "search_document: ", "query": "search_query: "}}

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        host = (os.environ.get("OLLAMA_HOST") or "http://localhost:11434").rstrip("/")
        host = host if host.startswith("http") else f"http://{host}"
        prefix = self.PREFIXES.get(self.model.split(":")[0], {}).get(_role, "")
        reply = _post_json(f"{host}/api/embed", {"model": self.model, "input": [prefix + t for t in texts]}, {},
                           service="Ollama", hint=f"Is `ollama serve` running, and has `ollama pull {self.model}` "
                                                  "been run?")
        return reply["embeddings"]


class VoyageClient(_Client):
    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        reply = _post_json("https://api.voyageai.com/v1/embeddings",
                           {"model": self.model, "input": texts, "input_type": _role},
                           {"Authorization": f"Bearer {_key('VOYAGE_API_KEY')}"}, service="Voyage AI")
        return [item["embedding"] for item in sorted(reply["data"], key=lambda item: item["index"])]


class OpenAIClient(_Client):
    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        reply = _post_json("https://api.openai.com/v1/embeddings", {"model": self.model, "input": texts},
                           {"Authorization": f"Bearer {_key('OPENAI_API_KEY')}"}, service="OpenAI")
        return [item["embedding"] for item in sorted(reply["data"], key=lambda item: item["index"])]


CLIENTS = {"ollama": OllamaClient, "voyage": VoyageClient, "openai": OpenAIClient}


def _key(name: str) -> str:
    value = (os.environ.get(name) or "").strip()
    if not value:
        raise EmbeddingError(f"Set {name} in .env to use this embedding provider (see .env.example).")
    return value


def _post_json(url: str, payload: dict, headers: dict, service: str, hint: str = "") -> dict:
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                     headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise EmbeddingError(f"{service} returned an error ({exc.code}): {detail} {hint}".strip()) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        reason = getattr(exc, "reason", exc)
        raise EmbeddingError(f"Could not reach {service} ({reason}). {hint}".strip()) from exc


def _unit(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    return [x / norm for x in vector] if norm else vector


# --------------------------------------------------------------------------- #
# Calibration
# --------------------------------------------------------------------------- #
def calibrate(matcher, job_descriptions: list[str]) -> dict:
    """The similarity band for an index's model, measured rather than assumed.

    Milestone 2 turns a candidate's raw similarity into its 0-1 semantic score through a
    fixed band, 0.15 to 0.65, chosen by hand for MiniLM. Another model scores on another
    scale: with that band its scores would bunch at 0 or 1 and Round 1 would lose most of
    its semantic signal, which would make any comparison with MiniLM unfair. The band here
    is the 10th to 95th percentile of the same raw score, over every resume, for every job
    description given.
    """
    raw_scores = []
    for jd in job_descriptions:
        for hits in matcher.semantic_search(jd, n_chunks=matcher.collection.count()).values():
            sims = [h["similarity"] for h in hits]  # best first
            # Milestone 2's raw semantic score (JobMatcher._semantic_component, before its band)
            raw_scores.append(0.6 * sims[0] + 0.4 * sum(sims[:3]) / len(sims[:3]))
    if len(raw_scores) < 10:
        raise EmbeddingError("Too few similarity scores to calibrate; index more resumes or job descriptions.")
    raw_scores.sort()
    floor = raw_scores[int(LOW_PERCENTILE * (len(raw_scores) - 1))]
    ceil = raw_scores[int(HIGH_PERCENTILE * (len(raw_scores) - 1))]
    return {"floor": round(floor, 4), "ceil": round(max(ceil, floor + 1e-3), 4), "scores": len(raw_scores),
            "method": f"{LOW_PERCENTILE:.0%}-{HIGH_PERCENTILE:.0%} percentile of raw semantic scores"}
