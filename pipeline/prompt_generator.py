"""Instantiates the SAPIC+ prompt framework for a protocol description.

One LLM call reads PromptFramework.md alongside the user's English protocol
description and fills in the framework — a structured specification of the
model to build (summary, crypto setup, roles, top-level process, lemmas).
The completed text is then used as the user prompt for the final SAPIC+
generation, replacing the raw description.

Returns None on any failure (missing framework file, API error, empty
reply), in which case the pipeline falls back to prompting with the raw
description as before.
"""

from openai import OpenAI

from . import config
from .knowledge import build_catalog, load_property_bits

_GENERATOR_INSTRUCTIONS = """\
You are an expert in security protocols and formal verification with the
Tamarin prover's SAPIC+ process calculus. Below is a prompt framework, a
catalog of available security-property lemmas, and an English description
of a security protocol.

Instantiate the framework for this protocol:
- Fill in every `⟨…⟩` placeholder with the protocol's actual details
  (roles, messages, primitives, events, lemmas), keeping the section
  structure of the framework.
- Follow every `[Instruction: …]` note while writing, then OMIT the
  instruction notes themselves from your output.
- Ground every detail in the protocol description; do not invent
  mechanisms, messages, or goals the description does not support.
- In the lemmas section, always require the executability lemma, then
  choose from the property catalog exactly those properties that test the
  security goals this protocol states or implies -- and no others. Name
  each chosen property as in the catalog and state it informally but
  precisely over the protocol's events.

Reply with ONLY the completed prompt text, nothing else.
"""


def generate_prompt(description: str) -> str | None:
    """Fill in the prompt framework for this description, or None on failure."""
    if not config.PROMPT_FRAMEWORK_FILE.exists():
        print(f"[prompt-gen] {config.PROMPT_FRAMEWORK_FILE.name} not found; "
              "using the raw description")
        return None
    framework = config.PROMPT_FRAMEWORK_FILE.read_text(
        encoding="utf-8", errors="replace"
    )
    catalog = build_catalog(load_property_bits(), label="Category")
    request = (
        _GENERATOR_INSTRUCTIONS
        + "\nPrompt framework:\n\"\"\"\n" + framework.strip() + "\n\"\"\"\n"
        + "\nProperty lemma catalog:\n\"\"\"" + catalog + "\n\"\"\"\n"
        + f'\nProtocol description:\n"""\n{description.strip()}\n"""'
    )
    try:
        response = OpenAI().chat.completions.create(
            model=config.PROMPT_GEN_MODEL,
            messages=[{"role": "user", "content": request}],
        )
        generated = (response.choices[0].message.content or "").strip()
    except Exception as exc:  # API errors must not kill the run
        print(f"[prompt-gen] generation call failed ({exc}); "
              "using the raw description")
        return None
    if not generated:
        print("[prompt-gen] empty reply; using the raw description")
        return None
    return generated
