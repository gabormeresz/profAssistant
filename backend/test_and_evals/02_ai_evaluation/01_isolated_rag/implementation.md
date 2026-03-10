# 01 — Isolated RAG Pipeline Testing: Implementation

## Scope

Section **2.1** — Measuring the retrieval quality of the RAG (Retrieval-Augmented Generation) pipeline independently from LLM generation. Tests the vector search capabilities of ChromaDB + `text-embedding-3-small` against controlled synthetic documents.

## Approach

| Aspect           | Detail                                                                                                                            |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Test type**    | Integration test with real OpenAI embeddings (no mocks)                                                                           |
| **Documents**    | 2 synthetic PDFs: English (Operating Systems, 10 chapters, 42 chunks) and Hungarian (Database Management, 10 chapters, 41 chunks) |
| **Queries**      | 34 total (17 per language): 8 direct factual, 6 paraphrased, 3 multi-chunk                                                        |
| **Ground truth** | Semi-automated — chunk dumps are generated, then queries and relevant chunk indices are **manually annotated**                    |
| **Isolation**    | Temporary ChromaDB directory per session — no pollution of production data                                                        |
| **Metrics**      | Hit Rate@5, MRR@5, per-category breakdown                                                                                         |

### Ground Truth Workflow (semi-automated)

The ground truth creation is **not fully automated**. Replicating the evaluation requires three steps:

1. **Generate PDFs** — `generate_test_pdfs.py` creates reproducible synthetic PDFs with distinct, factual content per chapter. No API key needed.
2. **Generate chunk dumps** — `generate_ground_truth.py` ingests PDFs through the **production `RAGPipeline`** (same `RecursiveCharacterTextSplitter`, same `text-embedding-3-small` embeddings, same ChromaDB ingestion logic — only the persist directory differs). Outputs `chunks_en.json` / `chunks_hu.json` to `tests/artifacts/`.
3. **Manually annotate ground truth** — Review the chunk dumps, write queries targeting specific factual content, and assign `relevant_chunk_indices` by inspecting which chunks contain the answer. The resulting `ground_truth_en.json` / `ground_truth_hu.json` are placed in `tests/artifacts/`.

> **Note**: Only Step 3 requires human effort. Steps 1–2 are scripted. The retrieval tests (`test_rag_retrieval.py`) are fully automated and run against the pre-existing ground truth.

**If `CHUNK_SIZE` or `CHUNK_OVERLAP` change**, re-run Steps 1–2 and repeat the manual annotation (Step 3).

## Test Files

| File                       | Tests | Purpose                                                                         |
| -------------------------- | ----- | ------------------------------------------------------------------------------- |
| `test_rag_retrieval.py`    | 35    | 17 EN queries + 17 HU queries (parametrized) + 1 aggregate/export               |
| `conftest.py`              | —     | Session-scoped fixtures: RAG pipeline, document ingestion, ground truth loading |
| `generate_test_pdfs.py`    | —     | Step 1: creates synthetic test PDFs (output in `artifacts/`)                    |
| `generate_ground_truth.py` | —     | Step 2: ingests PDFs and dumps chunks (output in `artifacts/`)                  |

**Total: 35 test cases**, all marked `@pytest.mark.llm` (require `OPENAI_API_KEY`).

## Key Design Decisions

1. **K=5 only** — Matches the production default `n_results=5` in `RAGPipeline.query()`. Adding multiple K values was considered but deferred to keep the evaluation focused on production-representative conditions.
2. **Real embeddings, no mocks** — The entire point is measuring `text-embedding-3-small` retrieval quality. Mock embeddings would defeat the purpose. All tests are `@pytest.mark.llm`.
3. **Session-scoped fixtures** — Documents are ingested once per test session. This minimises API calls to ~117 total (42 EN chunks + 41 HU chunks for ingestion, then 34 query embeddings).
4. **Chunk-index-based annotation** — Ground truth references chunk indices (not IDs), which are converted to full chunk IDs at test time. This is robust to session_id changes.
5. **50% minimum threshold** — The aggregate test asserts Hit Rate@5 ≥ 50%. This is a conservative floor; we expect much higher scores. The exact metrics are recorded in `rag_results.json` for analysis.
6. **Bilingual testing** — Separate metrics for English and Hungarian reveal whether `text-embedding-3-small` handles non-English content equally well.

## Measured Metrics

| Metric                     | Definition                                                                                            |
| -------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Hit Rate@5**             | Fraction of queries where at least one of the top-5 retrieved chunks is in the annotated relevant set |
| **MRR@5**                  | Mean Reciprocal Rank — average of `1/rank` of the first relevant chunk across all queries             |
| **Per-category breakdown** | Hit Rate and MRR split by query type (direct_factual, paraphrased, multi_chunk)                       |

## How to Run

### Retrieval tests (automated)

```bash
cd backend && source .venv/bin/activate

# Run all RAG evaluation tests
pytest test_and_evals/02_ai_evaluation/01_isolated_rag/tests/ -m llm -v -s

# Save output to log
pytest test_and_evals/02_ai_evaluation/01_isolated_rag/tests/ -m llm -v -s \
  2>&1 | tee test_and_evals/02_ai_evaluation/01_isolated_rag/tests/logs/rag_retrieval.log
```

### Full replication (if chunk config changes)

```bash
cd backend && source .venv/bin/activate

# Step 1: Generate synthetic PDFs (no API key needed)
python test_and_evals/02_ai_evaluation/01_isolated_rag/tests/generate_test_pdfs.py

# Step 2: Generate chunk dumps (requires OPENAI_API_KEY)
python test_and_evals/02_ai_evaluation/01_isolated_rag/tests/generate_ground_truth.py

# Step 3: MANUAL — review artifacts/chunks_*.json and update
#         artifacts/ground_truth_en.json + artifacts/ground_truth_hu.json
#         with queries and relevant_chunk_indices

# Step 4: Run retrieval tests
pytest test_and_evals/02_ai_evaluation/01_isolated_rag/tests/ -m llm -v -s
```

## Output

- `tests/artifacts/rag_results.json` — Full structured results with per-query details
- `tests/artifacts/test_document_en.pdf` — Generated English test PDF
- `tests/artifacts/test_document_hu.pdf` — Generated Hungarian test PDF
- `tests/artifacts/chunks_en.json` — Chunk dump from English PDF ingestion
- `tests/artifacts/chunks_hu.json` — Chunk dump from Hungarian PDF ingestion
- `tests/artifacts/ground_truth_en.json` — Manually annotated English queries with relevant chunk indices
- `tests/artifacts/ground_truth_hu.json` — Manually annotated Hungarian queries with relevant chunk indices
- `tests/logs/rag_retrieval.log` — Raw pytest output
- Console summary with Hit Rate, MRR, and per-category tables
