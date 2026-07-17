"""Validates SAPIC+ code by compiling it with tamarin-prover.

Two stages:
  1. "parse"   -- `tamarin-prover --parse-only`: fast, gives clean syntax errors.
  2. "compile" -- full `tamarin-prover` run: the SAPIC+ translation, derivation
     checks, and theory loading must complete successfully (exit code 0).

Wellformedness warnings do not fail the compile stage: the reference theories
in Benchmark/ trigger several of them (e.g. the State_* facts that SAPIC+'s
translation of pattern-matched in() produces), so they are accepted.
"""

import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from . import config

# Maude startup banner printed before the real compile output.
_MAUDE_PREAMBLE = re.compile(
    r"^(maude tool:| checking (version|installation):).*\n?", re.MULTILINE
)

# "[Theory X] Theory loaded" progress lines.
_PROGRESS_LINES = re.compile(r"^\[Theory [^\]]*\].*\n?", re.MULTILINE)


@dataclass
class ValidationResult:
    ok: bool
    stage: str  # "parse" or "compile": the stage that produced `output`
    output: str  # tamarin's stdout+stderr (the error message on failure)


def _run_tamarin(
    extra_args: list[str], path: Path, timeout: int
) -> tuple[bool, str]:
    proc = subprocess.run(
        [config.TAMARIN_BINARY, *extra_args, str(path)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = (proc.stdout + "\n" + proc.stderr).strip()
    # Hide the throwaway temp path so repair prompts stay clean.
    output = output.replace(str(path), "<theory.spthy>")
    return proc.returncode == 0, output


def validate_spthy(code: str) -> ValidationResult:
    """Parse, then fully compile the code with tamarin-prover."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".spthy", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        tmp_path = Path(f.name)
    stage = "parse"
    try:
        ok, output = _run_tamarin(["--parse-only"], tmp_path, config.TAMARIN_TIMEOUT_SECONDS)
        if not ok:
            return ValidationResult(ok=False, stage=stage, output=output)

        stage = "compile"
        ok, output = _run_tamarin([], tmp_path, config.TAMARIN_COMPILE_TIMEOUT_SECONDS)
        if ok:
            return ValidationResult(ok=True, stage=stage, output="")
        output = _PROGRESS_LINES.sub("", _MAUDE_PREAMBLE.sub("", output)).strip()
        return ValidationResult(ok=False, stage=stage, output=output)
    except subprocess.TimeoutExpired:
        return ValidationResult(
            ok=False,
            stage=stage,
            output=f"tamarin-prover timed out during the {stage} stage",
        )
    except FileNotFoundError:
        return ValidationResult(
            ok=False,
            stage=stage,
            output=f"tamarin-prover binary not found: {config.TAMARIN_BINARY}",
        )
    finally:
        tmp_path.unlink(missing_ok=True)
