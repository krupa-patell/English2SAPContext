"""Selects the ProtocolBits building blocks relevant to a protocol description.

Rather than embedding the entire ProtocolBits library in the system prompt,
one lightweight LLM call reads the English description against a catalog of
block names/summaries and picks the blocks that fit the scenario. The full
code of only those blocks is then embedded as reference material.

Falls back to the whole library if the selection call fails or returns
nothing usable, so generation never breaks because of this stage.
"""

import json
import re

from openai import OpenAI

from . import config
from .knowledge import ProtocolBit, load_protocol_bits

_COMMENT_RE = re.compile(r"/\*(.*?)\*/", re.DOTALL)
_JSON_ARRAY_RE = re.compile(r"\[.*?\]", re.DOTALL)

_SELECTOR_INSTRUCTIONS = """\
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


def _summarize(bit: ProtocolBit) -> str:
    """One-line summary of a block: its first /* ... */ comment, if any."""
    match = _COMMENT_RE.search(bit.code)
    if match:
        return " ".join(match.group(1).split())
    return "(no description)"


def _build_catalog(bits: list[ProtocolBit]) -> str:
    lines = []
    current_phase = None
    for bit in bits:
        if bit.phase != current_phase:
            lines.append(f"\nPhase {bit.phase}:")
            current_phase = bit.phase
        lines.append(f'- "{bit.name}": {_summarize(bit)}')
    return "\n".join(lines)


def _parse_selection(reply: str, bits: list[ProtocolBit]) -> list[ProtocolBit]:
    """Extract the JSON array of names from the reply and map it to blocks."""
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


def select_bits(description: str) -> list[ProtocolBit]:
    """Return the building blocks relevant to the description.

    On any failure (API error, unparseable reply, empty pick) returns the
    full library so the pipeline degrades to previous behavior.
    """
    bits = load_protocol_bits()
    prompt = (
        _SELECTOR_INSTRUCTIONS
        + "\nCatalog of building blocks:\n"
        + _build_catalog(bits)
        + f'\n\nProtocol description:\n"""\n{description.strip()}\n"""'
    )
    try:
        response = OpenAI().chat.completions.create(
            model=config.SELECTOR_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        reply = response.choices[0].message.content or ""
    except Exception as exc:  # network/auth/model errors must not kill the run
        print(f"[selector] selection call failed ({exc}); using full library")
        return bits

    selected = _parse_selection(reply, bits)
    if not selected:
        print("[selector] could not parse a selection; using full library")
        return bits
    return selected
