import json
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "data" / "catalog.json"


class Assessment(BaseModel):
    name: str
    url: str
    test_type: str = ""
    description: str = ""
    job_levels: list[str] = []
    languages: list[str] = []
    raw_text: str = ""

    @property
    def searchable_text(self) -> str:
        parts = [
            self.name,
            self.test_type,
            self.description,
            " ".join(self.job_levels),
            " ".join(self.languages),
            self.raw_text,
        ]
        return " ".join(p for p in parts if p).lower()


@lru_cache(maxsize=1)
def load_catalog() -> list[Assessment]:
    if not CATALOG_PATH.exists():
        raise RuntimeError(
            "Catalog file missing. Run `python scripts/scrape_shl.py` before starting the API."
        )
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return [Assessment(**item) for item in data]


def catalog_urls() -> set[str]:
    return {item.url for item in load_catalog()}
