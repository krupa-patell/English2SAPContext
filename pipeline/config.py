"""Central configuration for the SAPIC+ generation pipeline."""

import os
from pathlib import Path

# --- Directory layout -------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
PROTOCOL_BITS_DIR = ROOT_DIR / "ProtocolBits"
BENCHMARK_DIR = ROOT_DIR / "Benchmark"
INPUT_DIR = ROOT_DIR / "Input"
OUTPUT_DIR = ROOT_DIR / "Output"
NAMING_CONVENTIONS_FILE = ROOT_DIR / "NamingConventions.md"
PROMPT_FRAMEWORK_FILE = ROOT_DIR / "PromptFramework.md"

# --- LLM settings ------------------------------------------------------------
# Reads OPENAI_API_KEY from the environment (standard openai SDK behavior).
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5")

# Model for the cheap building-block selection call (defaults to OPENAI_MODEL).
SELECTOR_MODEL = os.environ.get("OPENAI_SELECTOR_MODEL", OPENAI_MODEL)

# Model that instantiates PromptFramework.md into the final generation prompt.
PROMPT_GEN_MODEL = os.environ.get("OPENAI_PROMPT_GEN_MODEL", OPENAI_MODEL)

# Benchmark protocols used as few-shot (description -> SAPIC+) examples in the
# prompt, ordered simplest first. Names refer to the .txt file stem.
FEW_SHOT_EXAMPLES = ["Example", "EDHOC", "Otway-Rees"]

# --- Validation / repair loop -----------------------------------------------
TAMARIN_BINARY = os.environ.get("TAMARIN_BINARY", "tamarin-prover")
TAMARIN_TIMEOUT_SECONDS = 120
# Total generation attempts = 1 initial + (MAX_REPAIR_ATTEMPTS) fix rounds.
MAX_REPAIR_ATTEMPTS = 3
