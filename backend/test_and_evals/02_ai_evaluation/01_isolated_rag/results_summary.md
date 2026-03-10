# Isolated RAG Pipeline — Results Summary

> **Status:** PASSED — 35/35 tests passed (2025-03-02)

## Configuration

| Parameter       | Value                    |
| --------------- | ------------------------ |
| Embedding model | `text-embedding-3-small` |
| Chunk size      | 500 chars                |
| Chunk overlap   | 100 chars                |
| Top-K           | 5                        |
| Min similarity  | 0.3                      |
| Distance metric | cosine                   |

## Test Corpus

| Document               | Language  | Chapters | Chunks | Topic                             |
| ---------------------- | --------- | -------- | ------ | --------------------------------- |
| `test_document_en.pdf` | English   | 10       | 42     | Introduction to Operating Systems |
| `test_document_hu.pdf` | Hungarian | 10       | 41     | Bevezetés az adatbázis-kezelésbe  |

## Results

Each language group is a self-contained evaluation: the document and all queries are in the same language (EN queries against the English PDF, HU queries against the Hungarian PDF). There is no cross-language retrieval testing.

| Metric         | English     | Hungarian  | Combined   |
| -------------- | ----------- | ---------- | ---------- |
| **Hit Rate@5** | **100.00%** | **94.12%** | **97.06%** |
| **MRR@5**      | **0.9706**  | **0.7373** | **0.8539** |
| Queries        | 17          | 17         | 34         |

### Per-Category Breakdown

| Category             | EN Hit Rate | EN MRR | HU Hit Rate | HU MRR |
| -------------------- | ----------- | ------ | ----------- | ------ |
| direct_factual (n=8) | 100.00%     | 1.0000 | 87.50%      | 0.8125 |
| paraphrased (n=6)    | 100.00%     | 0.9167 | 100.00%     | 0.5056 |
| multi_chunk (n=3)    | 100.00%     | 1.0000 | 100.00%     | 1.0000 |

## Key Findings

1. **Near-perfect English retrieval** — EN Hit Rate@5 = 100% and MRR = 0.97. With 10 chapters (42 chunks), the pipeline still retrieves the correct chunk at or near position #1 for all queries. `text-embedding-3-small` with 500-char chunks handles the larger corpus well.
2. **Hungarian retrieval slightly weaker** — HU Hit Rate@5 = 94.12% (1 miss in 17 relevant queries) and MRR = 0.74. This is expected for multilingual embeddings. Hungarian paraphrased queries show the largest gap (MRR=0.51), indicating that semantic similarity is less precisely calibrated for paraphrased Hungarian academic content.
3. **Multi-chunk queries perfect in both languages** — Queries requiring information from multiple chapters achieve 100% hit rate and 1.0 MRR, demonstrating that the chunking strategy preserves cross-topic retrievability.
4. **10-chapter documents provide meaningful evaluation** — With 42/41 chunks per document, the retrieval task is non-trivial. The pipeline must discriminate among ~80 total chunks to find the right ones.

## Log Reference

- Raw output: [`tests/logs/rag_retrieval.log`](tests/logs/rag_retrieval.log)
- Structured data: [`tests/artifacts/rag_results.json`](tests/artifacts/rag_results.json)
