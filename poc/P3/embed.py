"""P3b embedding spike: embed sheet chunks and questions, then measure recall@4.

    cd apps/api
    uv run python ../../poc/P3/chunking.py                                     # out/chunks.json
    uv run python ../../poc/P3/embed.py --model gemini:gemini-embedding-2
    uv run python ../../poc/P3/embed.py --model gemini:gemini-embedding-001
    uv run --with sentence-transformers python ../../poc/P3/embed.py --model local:BAAI/bge-m3

Every embedding goes through ``Gateway.embed`` (AI-01). Chunk vectors are cached per model in
out/embed/<model>/ next to each chunk's content_hash (AI-08), so a rerun only embeds new text.
Results (recall, dimensions, time; question ids only) go to results/embed-<model>.json.
"""

import argparse
import asyncio
import json
import math
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from chunking import Chunk

HERE = Path(__file__).parent
REPO = HERE.parents[1]
OUT = HERE / "out"  # gitignored: contains text of the course files
RESULTS = HERE / "results"
QUESTIONS = REPO / "evals" / "topics" / "mth10101" / "retrieval_questions.md"
K = 4  # recall@4: the PoC metric in specs/poc/README.md P3
# Free tier of gemini-embedding-2: 30K tokens per minute (ai.dev/rate-limit, 21 Oct). Stay under
# it with a margin, counting Thai at 1.5 characters per token (measured 1.47-1.82 on 5 chunks).
FREE_TIER_TOKENS_PER_MINUTE = 25_000
FREE_TIER_CHARS_PER_TOKEN = 1.5
LOCAL_TIMEOUT_S = 900  # one batch of 10 chunks on this laptop's CPU; measured time goes in results

_PAGE = re.compile(r"(sheet-\d+):(\d+)(?:-(\d+))?")


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    pages: list[tuple[str, int]]


def parse_questions(markdown: str) -> list[Question]:
    """Filled rows of the question table: a number, a question and at least one page."""
    questions = []
    for line in markdown.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not cells[0].isdigit() or not cells[1]:
            continue
        pages = [
            (file, page)
            for file, first, last in _PAGE.findall(cells[2])
            for page in range(int(first), int(last or first) + 1)
        ]
        if pages:
            questions.append(Question(id=cells[0], text=cells[1], pages=pages))
    return questions


def _cosine(a: list[float], b: list[float]) -> float:
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b, strict=True)) / norm if norm else 0.0


def rank(query: list[float], chunk_vectors: list[list[float]]) -> list[int]:
    """Chunk indexes from most to least similar to the query."""
    scores = [_cosine(query, vector) for vector in chunk_vectors]
    return sorted(range(len(scores)), key=lambda i: -scores[i])


def hit_at_k(question: Question, ranking: list[int], chunks: list[Chunk], k: int) -> bool:
    return any(
        chunks[i].file == file and chunks[i].page_from <= page <= chunks[i].page_to
        for i in ranking[:k]
        for file, page in question.pages
    )


def recall_at_k(
    questions: list[Question], rankings: list[list[int]], chunks: list[Chunk], k: int
) -> float:
    hits = [hit_at_k(q, r, chunks, k) for q, r in zip(questions, rankings, strict=True)]
    return sum(hits) / len(hits) if hits else 0.0


def run_name(model: str, dimensions: int | None) -> str:
    """Folder of the vector cache and name of the result file: one per model and vector size."""
    name = model.replace(":", "_").replace("/", "_")
    return f"{name}-d{dimensions}" if dimensions else name


# --- run ------------------------------------------------------------------------------------


class LocalEmbedder:
    """Open-source model on this machine (PoC only; needs ``uv run --with sentence-transformers``).
    Speaks the gateway's EmbedProvider interface so the call still goes through Gateway.embed."""

    def __init__(self) -> None:
        self._models: dict = {}

    def load(self, name: str):
        """Load once and keep; call before timing so the load is not counted as embed time."""
        if name not in self._models:
            from sentence_transformers import SentenceTransformer

            self._models[name] = SentenceTransformer(name)
        return self._models[name]

    async def embed(self, request):
        from app.ai.providers.base import EmbedResponse

        def encode():
            model = self.load(request.model)
            return model.encode(request.texts, normalize_embeddings=True).tolist()

        return EmbedResponse(vectors=await asyncio.to_thread(encode), tokens_in=0)


async def main(model: str, questions_path: Path, dimensions: int | None) -> None:
    sys.path.insert(0, str(REPO / "apps" / "api"))
    from app.ai.gateway import Gateway
    from app.ai.providers.gemini import GeminiProvider
    from app.settings import get_settings

    settings = get_settings()
    config = settings.ai
    local = LocalEmbedder()
    providers: dict = {"local": local}
    if model.startswith("gemini:"):
        providers["gemini"] = GeminiProvider(settings.env.gemini_api_key.get_secret_value())
    else:
        # A local model on CPU is far slower than an API call: PoC only, config/ai.yaml keeps
        # its timeout for the real system.
        config = config.model_copy(
            update={"embedding": config.embedding.model_copy(update={"timeout_s": LOCAL_TIMEOUT_S})}
        )
        await asyncio.to_thread(local.load, model.partition(":")[2])
    if dimensions:
        config = config.model_copy(
            update={"embedding": config.embedding.model_copy(update={"dimensions": dimensions})}
        )
    gateway = Gateway.live(config, settings.env.prompts_dir, providers, model)

    chunks = [Chunk(**c) for c in json.loads((OUT / "chunks.json").read_text(encoding="utf-8"))]
    questions = parse_questions(questions_path.read_text(encoding="utf-8"))
    if not questions:
        sys.exit(f"no filled questions in {questions_path}")

    name = run_name(model, dimensions)
    cache_path = OUT / "embed" / name / "chunks.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    todo = [c for c in chunks if c.content_hash not in cache]
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    chunk_seconds = 0.0
    used_tokens, window_start = 0, time.monotonic()
    step = settings.ai.embedding.batch_size
    for start in range(0, len(todo), step):
        part = todo[start : start + step]
        tokens = sum(len(c.text) for c in part) / FREE_TIER_CHARS_PER_TOKEN
        if model.startswith("gemini:") and used_tokens + tokens > FREE_TIER_TOKENS_PER_MINUTE:
            await asyncio.sleep(max(0.0, 60 - (time.monotonic() - window_start)))
            used_tokens, window_start = 0, time.monotonic()
        started = time.perf_counter()
        vectors = await gateway.embed([c.text for c in part], "document")
        chunk_seconds += time.perf_counter() - started
        used_tokens += tokens
        cache.update({c.content_hash: v for c, v in zip(part, vectors, strict=True)})
        cache_path.write_text(json.dumps(cache), encoding="utf-8")  # keep progress on errors

    started = time.perf_counter()
    query_vectors = await gateway.embed([q.text for q in questions], "query")
    query_seconds = time.perf_counter() - started

    chunk_vectors = [cache[c.content_hash] for c in chunks]
    rankings = [rank(v, chunk_vectors) for v in query_vectors]
    result = {
        "model": model,
        "questions": len(questions),
        "chunks": len(chunks),
        "dimensions": len(chunk_vectors[0]),
        "recall_at_1": recall_at_k(questions, rankings, chunks, 1),
        f"recall_at_{K}": recall_at_k(questions, rankings, chunks, K),
        "seconds_embed_new_chunks": round(chunk_seconds, 1),
        "new_chunks_embedded": len(todo),
        "seconds_per_question": round(query_seconds / len(questions), 3),
        "misses_at_k": [
            q.id for q, r in zip(questions, rankings, strict=True) if not hit_at_k(q, r, chunks, K)
        ],
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"embed-{name}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="gemini:<id> or local:<huggingface id>")
    parser.add_argument("--questions", type=Path, default=QUESTIONS)
    parser.add_argument(
        "--dimensions", type=int, default=None, help="vector size to ask for (default: model's)"
    )
    args = parser.parse_args()
    asyncio.run(main(args.model, args.questions, args.dimensions))
