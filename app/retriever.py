from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.catalog import Assessment


TECH_KEYWORDS = {
    "java": ["java"],
    "python": ["python"],
    "javascript": ["javascript", "js", "node"],
    "sql": ["sql", "database"],
    "c#": ["c#", ".net", "dotnet"],
    "excel": ["excel"],
    "sales": ["sales"],
    "customer": ["customer", "service"],
}

PERSONALITY_WORDS = ["personality", "behavior", "behaviour", "opq", "motivation"]
COGNITIVE_WORDS = ["cognitive", "ability", "gsa", "reasoning", "numerical", "verbal", "logical"]


@dataclass
class RankedAssessment:
    item: Assessment
    score: float


class CatalogRetriever:
    def __init__(self, catalog: list[Assessment]):
        self.catalog = catalog
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.matrix = self.vectorizer.fit_transform([a.searchable_text for a in catalog])

    def search(self, query: str, limit: int = 10) -> list[RankedAssessment]:
        query_l = query.lower()
        qv = self.vectorizer.transform([query_l])
        sims = cosine_similarity(qv, self.matrix).ravel()

        ranked: list[RankedAssessment] = []
        for idx, item in enumerate(self.catalog):
            score = float(sims[idx])
            text = item.searchable_text

            for skill, aliases in TECH_KEYWORDS.items():
                if any(alias in query_l for alias in aliases) and skill in text:
                    score += 0.45

            if any(w in query_l for w in PERSONALITY_WORDS):
                if "personality" in text or "opq" in text or item.test_type.upper() == "P":
                    score += 0.35

            if any(w in query_l for w in COGNITIVE_WORDS):
                if "ability" in text or "reasoning" in text or "gsa" in text:
                    score += 0.35

            if "graduate" in query_l and "graduate" in text:
                score += 0.2
            if ("manager" in query_l or "lead" in query_l) and ("manager" in text or "lead" in text):
                score += 0.2

            if score > 0:
                ranked.append(RankedAssessment(item=item, score=score))

        ranked.sort(key=lambda r: (r.score, exact_name_bonus(query_l, r.item.name)), reverse=True)
        return ranked[:limit]


def exact_name_bonus(query: str, name: str) -> int:
    return 1 if name.lower() in query else 0
