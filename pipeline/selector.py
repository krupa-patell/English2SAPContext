"""Selects the library bits relevant to a protocol description.

Two selections, each one lightweight LLM call over a catalog of
names/summaries:
  - select_bits: which ProtocolBits building blocks the protocol's
    mechanisms need (key setup, encryption style, handshake messages, ...).
  - select_lemmas: which PropertyBits lemma templates match the protocol's
    stated security goals. The executability lemma is always included.

Both fall back to a safe default if the selection call fails or returns
nothing usable, so generation never breaks because of this stage.
"""

import json
import re

from openai import OpenAI

from . import config
from .knowledge import (
    ProtocolBit,
    build_catalog,
    load_property_bits,
    load_protocol_bits,
)

_JSON_ARRAY_RE = re.compile(r"\[.*?\]", re.DOTALL)

_BITS_INSTRUCTIONS = """\
You are an expert in security protocols and the SAPIC+ process calculus.
Below is a catalog of reusable SAPIC+ building blocks, followed by an English
description of a protocol. Select every building block that models a
mechanism the protocol uses (key setup, nonces, encryption style, key
exchange, signatures, hashing/KDFs, handshake messages, session close, ...).

Rules:
- Choose only from the catalog names, exactly as written.
- Include a block if the protocol plausibly needs its pattern; when unsure,
  include it. Exclude blocks for mechanisms the protocol clearly does not use.
- Reply with ONLY a JSON array of the selected block names, nothing else.
"""

_LEMMA_INSTRUCTIONS = """\
You are an expert in formal verification of security protocols. Below is a
catalog of security-property lemma templates, followed by a description of a
protocol (and possibly the modelling instructions derived from it). Select
the lemma templates that test the security properties this protocol claims
or implies.

Rules:
- Choose only from the catalog names, exactly as written.
- "executability" is mandatory: always include it.
- Otherwise select by the protocol's stated goals: authentication goals ->
  the appropriate level of the authentication hierarchy; key establishment ->
  key secrecy/agreement/freshness properties; and so on. When the
  description names or implies a property, include its template; when unsure
  between adjacent strengths (e.g. injective vs. non-injective agreement),
  include both. Exclude properties the protocol clearly does not claim.
- Include sanity templates (non-vacuity, per-phase reachability) when they
  guard the selected properties against holding vacuously.
- Reply with ONLY a JSON array of the selected template names, nothing else.
"""

# Fallback lemma set: previous pipeline behavior (its four fixed lemmas).
_DEFAULT_LEMMAS = [
    "executability",
    "secrecy",
    "injective_agreement",
    "noninjective_agreement",
]


def _parse_selection(reply: str, bits: list[ProtocolBit]) -> list[ProtocolBit]:
    """Extract the JSON array of names from the reply and map it to bits."""
    match = _JSON_ARRAY_RE.search(reply)
    if match is None:
        return []
    try:
        names = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    if not isinstance(names, list):
        return []
    wanted = {str(n).strip().lower() for n in names}
    return [bit for bit in bits if bit.name.lower() in wanted]


def _select(instructions: str, catalog: str, text: str) -> str | None:
    """Run one selection call; returns the raw reply or None on failure."""
    prompt = (
        instructions
        + "\nCatalog:\n"
        + catalog
        + f'\n\nProtocol description:\n"""\n{text.strip()}\n"""'
    )
    try:
        response = OpenAI().chat.completions.create(
            model=config.SELECTOR_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""
    except Exception as exc:  # network/auth/model errors must not kill the run
        print(f"[selector] selection call failed ({exc})")
        return None


def select_bits(description: str) -> list[ProtocolBit]:
    """Return the building blocks relevant to the description.

    On any failure (API error, unparseable reply, empty pick) returns the
    full library so the pipeline degrades to previous behavior.
    """
    bits = load_protocol_bits()
    reply = _select(_BITS_INSTRUCTIONS, build_catalog(bits), description)
    if reply is None:
        print("[selector] using the full building-block library")
        return bits
    selected = _parse_selection(reply, bits)
    if not selected:
        print("[selector] could not parse a selection; using full library")
        return bits
    return selected


def select_lemmas(text: str) -> list[ProtocolBit]:
    """Return the property lemma templates matching the protocol's goals.

    `text` is ideally the instantiated framework prompt (which states the
    goals explicitly), falling back to the raw description. Executability is
    always part of the result. On any failure returns the default core set
    (the four lemmas the pipeline previously mandated).
    """
    bits = load_property_bits()
    reply = _select(
        _LEMMA_INSTRUCTIONS, build_catalog(bits, label="Category"), text
    )
    selected = _parse_selection(reply, bits) if reply is not None else []
    if not selected:
        print("[selector] no usable lemma selection; using the default set")
        selected = [bit for bit in bits if bit.name in _DEFAULT_LEMMAS]
    if not any(bit.name == "executability" for bit in selected):
        selected += [bit for bit in bits if bit.name == "executability"]
    return selected
