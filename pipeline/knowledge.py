"""Loads the SAPIC+ knowledge base: ProtocolBits building blocks,
PropertyBits lemma templates, and Benchmark ground-truth (English
description, SAPIC+ code) example pairs."""

import re
from dataclasses import dataclass
from pathlib import Path

from . import config

_COMMENT_RE = re.compile(r"/\*(.*?)\*/", re.DOTALL)


@dataclass
class ProtocolBit:
    phase: str      # e.g. "1) Startup"
    name: str       # e.g. "nonce"
    code: str


@dataclass
class BenchmarkExample:
    name: str
    description: str
    code: str


def _load_bits(root: Path) -> list[ProtocolBit]:
    """Load every .spthy under a bits library, grouped by subfolder."""
    bits = []
    for phase_dir in sorted(root.iterdir()):
        if not phase_dir.is_dir():
            continue
        for spthy in sorted(phase_dir.glob("*.spthy")):
            bits.append(ProtocolBit(
                phase=phase_dir.name,
                name=spthy.stem,
                code=spthy.read_text(encoding="utf-8", errors="replace"),
            ))
    return bits


def load_protocol_bits() -> list[ProtocolBit]:
    """Load the ProtocolBits building-block library."""
    return _load_bits(config.PROTOCOL_BITS_DIR)


def load_property_bits() -> list[ProtocolBit]:
    """Load the PropertyBits security-property lemma-template library."""
    return _load_bits(config.PROPERTY_BITS_DIR)


def summarize_bit(bit: ProtocolBit) -> str:
    """One-line summary of a bit: its first /* ... */ comment, if any."""
    match = _COMMENT_RE.search(bit.code)
    if match:
        return " ".join(match.group(1).split())
    return "(no description)"


def build_catalog(bits: list[ProtocolBit], label: str = "Phase") -> str:
    """Render bits as a name+summary catalog, grouped by phase/category."""
    lines = []
    current_phase = None
    for bit in bits:
        if bit.phase != current_phase:
            lines.append(f"\n{label} {bit.phase}:")
            current_phase = bit.phase
        lines.append(f'- "{bit.name}": {summarize_bit(bit)}')
    return "\n".join(lines)


def _find_spthy_for(txt_path: Path) -> Path | None:
    """Find the ground-truth <name>-P.spthy that pairs with a description .txt.

    Handles naming drift like "Kao-Chow v1.txt" -> "Kao-Chow-P.spthy" and
    "CCITT-X509-1.txt" -> "CCITT-X509-P.spthy".
    """
    stem = txt_path.stem
    candidates = [stem, stem.split(" ")[0], stem.rsplit("-", 1)[0]]
    for cand in candidates:
        p = txt_path.parent / f"{cand}-P.spthy"
        if p.exists():
            return p
    return None


def load_benchmark_examples(names: list[str] | None = None) -> list[BenchmarkExample]:
    """Load (description, code) pairs from the Benchmark folder.

    If names is given, only those protocols are loaded, in the given order;
    otherwise every pair found is returned.
    """
    examples = []
    txt_files = {p.stem: p for p in config.BENCHMARK_DIR.glob("*.txt")}
    wanted = names if names is not None else sorted(txt_files)
    for name in wanted:
        txt = txt_files.get(name)
        if txt is None:
            continue
        spthy = _find_spthy_for(txt)
        if spthy is None:
            continue
        examples.append(BenchmarkExample(
            name=name,
            description=txt.read_text(encoding="utf-8", errors="replace"),
            code=spthy.read_text(encoding="utf-8", errors="replace"),
        ))
    return examples
