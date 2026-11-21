Test set: 82 posts · run 2026-11-21T21:25:06 · commit 20a88e7-dirty

| Model | Macro-F1 | Macro-F1 (general / keyword) | Latency p50 / p95 | Tokens in / out per item |
| :--- | ---: | :--- | :--- | :--- |
| TF-IDF + LR baseline | 0.433 | 0.421 / 0.452 | 0.03 ms | – |
| gemini-3.5-flash-lite (zero-shot) | 0.644 | 0.605 / 0.652 | 1.703 s / 7.169 s | 1097.7 / 211.5 |

LLM: 0 failed answers, ungrounded evidence 0.0, 2 of 246 questions flagged as advice, priority-check rule met in 0.9821 of 56 applicable notes.
