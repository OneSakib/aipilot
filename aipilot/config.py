import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    models_file: Path
    skills_dir: Path
    workspace: Path
    max_steps: int
    command_timeout: int
    max_output_chars: int


@lru_cache
def get_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv()
    return Settings(
        models_file=Path(os.getenv("AIPILOT_MODELS_FILE", PROJECT_ROOT / "models.yaml")),
        skills_dir=Path(os.getenv("AIPILOT_SKILLS_DIR", PROJECT_ROOT / "skills")),
        workspace=Path(os.getenv("AIPILOT_WORKSPACE", ".")).resolve(),
        max_steps=int(os.getenv("AIPILOT_MAX_STEPS", "25")),
        command_timeout=int(os.getenv("AIPILOT_COMMAND_TIMEOUT", "120")),
        max_output_chars=int(os.getenv("AIPILOT_MAX_OUTPUT_CHARS", "12000")),
    )
