import json
import uuid
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
TASK2_SEED_PATH = ROOT_DIR / "seed_data" / "task2" / "OSS_Mapping_Seed.json"

UUID_NAMESPACE = uuid.UUID("7fb7cb8f-9536-41f6-a908-80fa31d8dc2d")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_task2_seed() -> dict[str, Any]:
    return load_json(TASK2_SEED_PATH)


def uuid_from_token(token: str) -> uuid.UUID:
    return uuid.uuid5(UUID_NAMESPACE, token)
