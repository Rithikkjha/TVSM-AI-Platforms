# LinkedIn Post — "The RAG mistake nobody talks about: retrieving the right thing, then throwing it away"

> Draft for LinkedIn. Two versions below: a longer article and a short punchy post.
> Swap in your own voice, add a diagram/screenshot, and tag your team.

---

## Version A — Long-form article

**We built an AI that answers questions about hundreds of microservices. Then I found a bug that quietly wasted our smartest component.**

At TVS Motor we're building an internal "engineering brain" — ask it *"how does the payment update flow work in the booking service?"* and it answers in plain English, grounded in our real code, tickets, and docs. Under the hood it's a GraphRAG system: a vector database for meaning, a graph database for how services connect, and an LLM to write the answer.

It worked well. Until I traced one question end to end and noticed something embarrassing.

**The setup**

Good retrieval is a funnel. You cast a wide net, then narrow ruthlessly:

1. Search a big pile of small text "chunks" — using *both* semantic search (meaning) and keyword search (exact terms like service names and error codes).
2. Merge the two result lists.
3. Run a "re-ranker" — a model that re-scores the top 30 candidates and keeps the best 5. This is the precision step. It's the expensive, smart part.

So far, textbook.

**The mistake**

At the final step, instead of sending those 5 carefully-chosen snippets to the LLM, our code fetched the **entire parent document** for each — the whole 15,000-character file — and sent all of that.

Read that again. We spent real compute picking the 5 best *paragraphs*… then threw them away and sent the 5 best *whole documents* instead.

For a simple "tell me about service X" question, no harm done — one small doc fits fine. But for the questions that actually matter — *"walk me through the end-to-end payment flow across booking, payments, and notifications"* — we'd pull four or five giant documents, blow past the context limit, and the system would **silently truncate** the very section that answered the question. The precision we paid for was wasted, and sometimes the answer got cut off.

**What the industry already figured out**

Turns out this is a solved problem, and the pattern has a name: **Parent-Document Retrieval** (and its cousin, **Auto-Merging Retrieval**). The idea:

- Index **small** chunks — small text embeds more accurately.
- But at answer time, send a **bigger, coherent unit** — because the model needs surrounding context, not a lone sentence.

The trick is choosing *how big*. That's **granularity**:

```
chunk   →   section   →   full document
(precise)   (balanced)    (complete but heavy)
```

And the decision rule is a **token budget**. A recent paper (arXiv 2510.20609) found the crossover neatly: small units win when you're tight on budget; whole documents only become worth it around ~16K tokens of context. Microsoft's own RAG guidance is blunt: stuffing entire documents is expensive, overflows limits, and gives worse answers.

**Our fix**

Make granularity adaptive, decided by measured facts — not guesswork:

- If the documents we picked **fit** the token budget → send them whole (completeness, no downside).
- If they'd **overflow** → drop to **section-level**: pull just the relevant section from each document, highest-relevance first, until the budget is full.

So *"tell me about payments in booking"* still gets rich context, but *"end-to-end flow across five services"* now fits **all five** services' relevant sections in the window — instead of three full docs and a truncated fourth.

**The part most people skip: the graph**

One more thing that makes cross-service answers possible. Plain RAG finds text that *looks* similar to your question. But "how does booking talk to payments?" isn't a similarity problem — it's a *relationship* problem. So we also walk a dependency graph (`booking —DEPENDS_ON→ payments`) to pull in connected services even when their text doesn't resemble the question. Industry benchmarks put this "context-graph" approach at meaningfully higher accuracy than flat chunk retrieval.

**The uncomfortable lesson**

The fanciest part of your pipeline is worthless if the last step undoes it. Retrieval quality isn't just "did I find the right thing" — it's "did I actually *deliver* the right thing to the model, in the right size, within the budget."

Precision you don't preserve is precision you didn't have.

*Building internal AI tooling? I'd love to compare notes on RAG in the real world — the gap between the demo and production is mostly in these unglamorous details.*

#RAG #LLM #AIEngineering #GraphRAG #MachineLearning #SoftwareEngineering

---

## Version B — Short punchy post

We built an internal AI that answers questions about hundreds of microservices.

Then I found a bug that quietly wasted our smartest component.

The pipeline did everything right:
→ search small text chunks (meaning + keywords)
→ merge the results
→ run a re-ranker to pick the 5 best snippets

…and then, at the final step, **threw those snippets away** and sent the LLM the 5 entire documents they came from instead. 15,000 characters each.

For "tell me about service X" — fine, one doc fits.
For "walk me through the payment flow across 5 services" — disaster. The documents overflowed the context window, and the system silently truncated the exact section that held the answer.

We paid for precision, then deleted it.

The fix is a pattern the field already knows — **parent-document / auto-merging retrieval** with a **token budget**:

• Documents fit the budget? Send them whole.
• Would they overflow? Send just the relevant *section* of each, best-first, until the budget's full.

Simple idea. Big difference on exactly the questions that matter most.

The lesson I keep relearning: the fanciest part of your system is worthless if the last step undoes it.

Precision you don't preserve is precision you never had.

#RAG #LLM #AIEngineering #GraphRAG

---

## Notes for posting
- **No confidential specifics**: this draft keeps everything generic (no TVS internal service names, credentials, or metrics). Safe to post publicly. Double-check before publishing.
- Add a simple visual: the `chunk → section → full document` ladder, or a before/after of the funnel. Diagrams lift reach a lot.
- Best length for LinkedIn engagement is usually the short version (B). Use A as a Medium/blog article and link it.
- Consider ending with a genuine question to invite comments (already included).
