import json
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "data" / "catalog.json"


class Assessment(BaseModel):
    name: str
    url: str = ""
    test_type: str = ""
    description: str = ""
    job_levels: list[str] = []
    languages: list[str] = []
    raw_text: str = ""
    duration: str = ""
    remote: str = ""
    adaptive: str = ""
    keys: list[str] = []

    @property
    def searchable_text(self) -> str:
        parts = [
            self.name,
            self.test_type,
            self.description,
            " ".join(self.job_levels),
            " ".join(self.languages),
            self.duration,
            self.remote,
            self.adaptive,
            " ".join(self.keys),
            self.raw_text,
        ]
        return " ".join(p for p in parts if p).lower()


@lru_cache(maxsize=1)
def load_catalog() -> list[Assessment]:
    if not CATALOG_PATH.exists():
        raise RuntimeError(
            "Catalog file missing. Run `python scripts/scrape_shl.py` before starting the API."
        )
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"), strict=False)
    return [normalize_assessment(item) for item in data]


def catalog_urls() -> set[str]:
    return {item.url for item in load_catalog()}


def normalize_assessment(item: dict) -> Assessment:
    url = item.get("url") or item.get("link") or ""
    keys = item.get("keys") or []
    description = item.get("description") or ""
    raw_parts = [
        item.get("name", ""),
        description,
        " ".join(keys),
        item.get("duration", ""),
        item.get("remote", ""),
        item.get("adaptive", ""),
        item.get("job_levels_raw", ""),
        item.get("languages_raw", ""),
    ]
    return Assessment(
        name=item.get("name", ""),
        url=url,
        test_type=item.get("test_type") or infer_test_type(keys, description, item.get("name", "")),
        description=description,
        job_levels=item.get("job_levels") or [],
        languages=item.get("languages") or [],
        raw_text=item.get("raw_text") or " ".join(str(p) for p in raw_parts if p),
        duration=item.get("duration") or "",
        remote=item.get("remote") or "",
        adaptive=item.get("adaptive") or "",
        keys=keys,
    )


def infer_test_type(keys: list[str], description: str, name: str) -> str:
    text = " ".join(keys + [description, name]).lower()
    types: list[str] = []
    if "knowledge" in text or "skills" in text:
        types.append("K")
    if "personality" in text or "behavior" in text:
        types.append("P")
    if "ability" in text or "aptitude" in text:
        types.append("A")
    if "situational" in text or "biodata" in text:
        types.append("B")
    if "simulation" in text or "assessment exercises" in text:
        types.append("S")
    if "competenc" in text:
        types.append("C")
    if "development" in text or "360" in text:
        types.append("D")
    return " ".join(dict.fromkeys(types)) or "Unknown"
