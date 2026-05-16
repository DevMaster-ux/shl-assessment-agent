# Approach

This service uses a deterministic retrieval-first design instead of allowing a language model to invent answers. The SHL product catalog is scraped into `data/catalog.json`, and the API only recommends rows from that file. This directly protects the hard evaluator requirements: schema compliance, catalog-only recommendations, and valid SHL URLs.

The chat endpoint is stateless. Every request contains the full message history, so the agent reconstructs the latest intent from all user messages. Vague requests trigger a clarification question. Once the user gives a role, skill, seniority, or assessment focus, the retriever ranks assessments with TF-IDF plus small domain-specific boosts for skills, personality, cognitive ability, and seniority signals. Mid-conversation edits are handled naturally because the whole history is re-read on every call.

Comparison requests are routed separately. The agent finds mentioned assessment names in the catalog and answers from the scraped catalog descriptions and raw page text. Off-topic requests, legal advice, general hiring advice, and prompt-injection attempts return a refusal with an empty recommendation list.

I chose FastAPI because the assessment explicitly requires it and because it keeps the endpoint schema simple. I avoided a hosted LLM dependency for the core recommendation path so the service stays fast under the 30 second timeout and does not fail due to API limits. The design can still be improved by adding a small curated synonym table for the public traces after measuring Recall@10 locally.

What did not work well: relying only on keyword search is weak when users describe jobs naturally. A pure LLM approach is also risky because it may hallucinate assessment names or URLs. The final design combines lexical retrieval with controlled ranking rules and catalog-only output.
