"""Translates a user's English protocol description into LLM prompts.

Builds three things:
  - a system prompt embedding the ProtocolBits library and few-shot
    benchmark examples,
  - the initial user prompt from the English description,
  - repair prompts that feed tamarin-prover errors back for another attempt.
"""

from . import config
from .knowledge import (
    ProtocolBit,
    load_benchmark_examples,
    load_property_bits,
    load_protocol_bits,
)

SYSTEM_HEADER = """\
You are an expert in formal verification of security protocols using the
Tamarin prover's SAPIC+ process calculus. Your task: translate an English
description of a security protocol into a complete, syntactically valid
SAPIC+ theory (.spthy file) that compiles with tamarin-prover: it must
parse and the full SAPIC+ translation must load successfully.

Requirements for every theory you produce:
- Start with `theory <name>` / `begin` and finish with `end`.
- Declare needed `builtins:` following the built-in theory selection rules
  below, plus any custom `functions:`.
- Model each role as a `let <Role>(...) = ...` process using new/in/out/let/event.
- Compose roles under `process:` (e.g. `new k; (!A(k) | !B(k))`).
- Emit `event` actions at protocol milestones so lemmas can reference them.
- ALWAYS include an `exists-trace` executability lemma showing one complete
  honest run; it is the only lemma mandatory for every protocol.
- Add further security-property lemmas exactly as the prompt directs,
  adapting the property lemma templates below to the protocol's events. Do
  not add properties the protocol does not claim.
- Name variables according to the naming conventions below whenever the
  protocol has a matching concept; only deviate for concepts the
  conventions do not cover (following their style, e.g. role suffixes).
- Output the theory inside a single ```spthy fenced code block and nothing
  else outside it besides brief notes.

Below is a library of reusable SAPIC+ "building blocks", pre-selected as
relevant to the protocol at hand. Reuse their patterns (adapted to the
protocol) whenever they fit.
"""


def _format_naming_conventions() -> str:
    if not config.NAMING_CONVENTIONS_FILE.exists():
        return ""
    conventions = config.NAMING_CONVENTIONS_FILE.read_text(
        encoding="utf-8", errors="replace"
    )
    return f"\n# Naming conventions\n\n{conventions.strip()}\n"


def _format_builtin_rules() -> str:
    if not config.BUILTIN_RULES_FILE.exists():
        return ""
    rules = config.BUILTIN_RULES_FILE.read_text(encoding="utf-8", errors="replace")
    return (
        "\n# Built-in theory selection rules\n\n"
        "Use the following reference when deciding which `builtins:` your\n"
        "theory declares. Where it describes a standalone task (listing,\n"
        "mapping, justifying), apply its rules and mapping hints to the\n"
        "theory you produce instead of replying with a builtins line alone.\n\n"
        f"{rules.strip()}\n"
    )


def _format_bits(bits: list[ProtocolBit]) -> str:
    parts = []
    current_phase = None
    for bit in bits:
        if bit.phase != current_phase:
            parts.append(f"\n## Phase: {bit.phase}\n")
            current_phase = bit.phase
        parts.append(f"### Building block: {bit.name}\n```spthy\n{bit.code.strip()}\n```\n")
    return "".join(parts)


def _format_lemma_bits(bits: list[ProtocolBit]) -> str:
    parts = [
        "\n# Property lemma templates\n\n"
        "The following lemma templates cover the security properties selected "
        "for this protocol. When the prompt asks for one of these properties, "
        "adapt its template: keep the logical shape, rename events and adjust "
        "arities/argument order to the events your processes actually emit, "
        "and make sure every referenced event is emitted at the semantically "
        "correct point. If the prompt's compromise scenario models no key "
        "compromise, drop the Reveal/Honest escape clauses from the adapted "
        "lemmas (they must appear either consistently everywhere or not at "
        "all).\n"
    ]
    current_phase = None
    for bit in bits:
        if bit.phase != current_phase:
            parts.append(f"\n## Category: {bit.phase}\n")
            current_phase = bit.phase
        parts.append(
            f"### Lemma template: {bit.name}\n```spthy\n{bit.code.strip()}\n```\n"
        )
    return "".join(parts)


def _format_examples() -> str:
    parts = ["\nHere are complete worked examples of the translation task:\n"]
    for ex in load_benchmark_examples(config.FEW_SHOT_EXAMPLES):
        parts.append(
            f"\n## Example: {ex.name}\n"
            f"English description:\n\"\"\"\n{ex.description.strip()}\n\"\"\"\n"
            f"SAPIC+ translation:\n```spthy\n{ex.code.strip()}\n```\n"
        )
    return "".join(parts)


def build_system_prompt(
    bits: list[ProtocolBit] | None = None,
    lemma_bits: list[ProtocolBit] | None = None,
) -> str:
    """Build the system prompt around the given building blocks and lemmas.

    `bits`/`lemma_bits` are normally the selector's per-protocol picks; None
    embeds the whole ProtocolBits/PropertyBits library (e.g. for --dry-run,
    which makes no API calls).
    """
    if bits is None:
        bits = load_protocol_bits()
    if lemma_bits is None:
        lemma_bits = load_property_bits()
    return (
        SYSTEM_HEADER
        + _format_naming_conventions()
        + _format_builtin_rules()
        + _format_bits(bits)
        + _format_lemma_bits(lemma_bits)
        + _format_examples()
    )


def build_user_prompt(description: str) -> str:
    return (
        "Translate the following English protocol description into a SAPIC+ "
        "theory. Identify the roles, the messages exchanged, the cryptographic "
        "primitives used, and the intended security goals, then produce the "
        "complete .spthy file.\n\n"
        f"Protocol description:\n\"\"\"\n{description.strip()}\n\"\"\""
    )


def build_repair_prompt(error_output: str, stage: str = "parse") -> str:
    if stage == "compile":
        intro = (
            "The SAPIC+ theory you produced parses, but tamarin-prover failed "
            "while compiling it (loading and translating the theory). "
            "It reported:"
        )
    else:
        intro = (
            "The SAPIC+ theory you produced failed to parse. "
            "`tamarin-prover --parse-only` reported:"
        )
    return (
        f"{intro}\n\n"
        f"```\n{error_output.strip()}\n```\n\n"
        "Fix the error and output the full corrected theory in a single "
        "```spthy fenced code block. Do not omit any part of the theory."
    )
