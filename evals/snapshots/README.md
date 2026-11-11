# Offline snapshots

These JSONL files are outputs of the deterministic offline provider. That provider uses a hashing embedder, FAISS retrieval, and either the extractive fake generator or the unguarded fake generator.

They are not RAGAS judge scores. This directory does not contain faithfulness, answer relevancy, context precision, or context recall numbers from a live judge. No live OpenAI run was executed to produce these files, so those scores were not filled in.

`improved.jsonl` is the guarded retriever. `baseline.jsonl` is the inverted retriever with the unguarded fake provider.
