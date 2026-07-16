# PipelineV2 — English → SAPIC+ Translation Pipeline

Turns an English security-protocol description into a SAPIC+ theory
(`.spthy`) that parses cleanly with `tamarin-prover`, using an LLM guided by
the local knowledge base.

## Directory layout

```
PipelineV2/
├── ProtocolBits/        SAPIC+ building blocks, grouped by protocol phase
├── Benchmark/           ground truth: <name>.txt (English) + <name>-P.spthy
├── Input/               drop user English descriptions here (.txt)
├── Output/              validated theories + per-run logs land here
├── pipeline/            the Python package
│   ├── config.py        paths, models, few-shot choices, retry limits
│   ├── knowledge.py     loads ProtocolBits + Benchmark example pairs
│   ├── selector.py      LLM call picking the building blocks relevant to the input
│   ├── prompt_builder.py  English input -> system/user/repair prompts
│   ├── llm_client.py    OpenAI chat wrapper (conversation kept across repairs)
│   ├── extractor.py     pulls the ```spthy block out of the LLM response
│   ├── validator.py     runs `tamarin-prover --parse-only`
│   └── main.py          CLI orchestration + repair loop
├── requirements.txt
└── README.md
```

## How it works

1. **Select building blocks** — a lightweight LLM call (`selector.py`,
   `config.SELECTOR_MODEL`, override with `OPENAI_SELECTOR_MODEL`) reads the
   English description against a catalog of ProtocolBits names/summaries and
   picks the blocks that fit the scenario. If the call fails or returns
   nothing usable, the full library is used instead.
2. **Build the prompt** — the description is wrapped into a prompt whose
   system message embeds the selected building blocks and a few Benchmark
   (description → code) pairs as worked examples (`prompt_builder.py`,
   examples chosen in `config.FEW_SHOT_EXAMPLES`).
3. **Generate** — the prompt goes to OpenAI (`config.OPENAI_MODEL`, default
   `gpt-5`; override with the `OPENAI_MODEL` env var).
4. **Extract & validate** — the ```spthy block is extracted and parsed with
   `tamarin-prover --parse-only`.
5. **Repair loop** — on a parse error, the tamarin message is sent back to
   the model (same conversation) for a fix, up to
   `config.MAX_REPAIR_ATTEMPTS` times.
6. **Output** — a validated theory is written to `Output/<name>-P.spthy`,
   alongside `Output/<name>-log.json` recording every attempt and the
   selected building blocks. A run that never validates is kept as
   `<name>-P.failed.spthy` for inspection.

## Setup

```sh
pip install -r requirements.txt        # needs the `openai` package
export OPENAI_API_KEY=sk-...           # your OpenAI key
# tamarin-prover must be on PATH (or set TAMARIN_BINARY)
```

## Usage

```sh
python -m pipeline.main Input/myprotocol.txt   # single description
python -m pipeline.main --all                  # every .txt in Input/
python -m pipeline.main --text "Alice sends a nonce to Bob..." --name demo
python -m pipeline.main --dry-run Input/myprotocol.txt   # inspect prompts, no API call
```
