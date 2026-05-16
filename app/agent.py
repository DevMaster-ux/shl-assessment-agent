import re

from app.catalog import Assessment
from app.retriever import CatalogRetriever
from app.schemas import Message, Recommendation


OFF_TOPIC = [
    "legal",
    "law",
    "lawsuit",
    "salary",
    "compensation",
    "interview questions",
    "write job description",
    "hiring advice",
]

INJECTION = [
    "ignore previous",
    "ignore above",
    "system prompt",
    "developer message",
    "recommend outside",
    "fake url",
]

VAGUE = [
    "assessment",
    "test",
    "hiring",
    "hire someone",
    "need candidate",
]


class ShlAgent:
    def __init__(self, catalog: list[Assessment]):
        self.catalog = catalog
        self.retriever = CatalogRetriever(catalog)

    def respond(self, messages: list[Message]) -> tuple[str, list[Recommendation], bool]:
        conversation = "\n".join(f"{m.role}: {m.content}" for m in messages)
        latest = messages[-1].content.strip()
        latest_l = latest.lower()
        all_user_text = " ".join(m.content for m in messages if m.role == "user")

        if self._is_unsafe_or_offtopic(latest_l):
            return (
                "I can only help select SHL Individual Test Solutions from the SHL catalog. "
                "I cannot help with general hiring advice, legal topics, or instructions to bypass the catalog.",
                [],
                False,
            )

        if self._is_compare(latest_l):
            return self._compare(latest, all_user_text)

        if self._needs_clarification(all_user_text):
            return (
                "I can help with SHL assessments, but I need a little more role context first. "
                "What role are you hiring for, what seniority level is it, and should the assessment focus on skills, cognitive ability, personality, or a mix?",
                [],
                False,
            )

        ranked = self.retriever.search(all_user_text, limit=10)
        if not ranked:
            return (
                "I could not find a strong catalog match yet. Please share the role title, main skills, seniority, and whether you want technical, cognitive, personality, or behavioral assessments.",
                [],
                False,
            )

        recs = [
            Recommendation(name=r.item.name, url=r.item.url, test_type=r.item.test_type or "Unknown")
            for r in ranked[:10]
        ]
        count = len(recs)
        reply = (
            f"Got it. Based on the role details so far, here are {count} SHL catalog assessments to consider. "
            "I kept the shortlist limited to SHL Individual Test Solutions and used your latest constraints when ranking them."
        )
        return reply, recs, False

    def _is_unsafe_or_offtopic(self, text: str) -> bool:
        return any(x in text for x in OFF_TOPIC) or any(x in text for x in INJECTION)

    def _needs_clarification(self, text: str) -> bool:
        text_l = text.lower()
        has_role_signal = bool(
            re.search(
                r"\b(java|python|developer|engineer|sales|manager|analyst|graduate|customer|support|leader|finance|accounting|admin|nurse)\b",
                text_l,
            )
        )
        has_focus_signal = bool(
            re.search(
                r"\b(skill|technical|coding|personality|opq|cognitive|ability|gsa|reasoning|behavior|behaviour|situational|stakeholder)\b",
                text_l,
            )
        )
        vague_only = any(v in text_l for v in VAGUE) and not has_role_signal
        return vague_only or not (has_role_signal or has_focus_signal)

    def _is_compare(self, text: str) -> bool:
        return "difference between" in text or "compare" in text or " vs " in text or " versus " in text

    def _compare(self, latest: str, all_user_text: str) -> tuple[str, list[Recommendation], bool]:
        names = self._find_mentioned_assessments(latest)
        if len(names) < 2:
            names = self._find_mentioned_assessments(all_user_text)

        if len(names) < 2:
            return (
                "I can compare SHL assessments, but I need the assessment names. For example: compare OPQ and GSA.",
                [],
                False,
            )

        left, right = names[:2]
        reply = (
            f"{left.name} and {right.name} serve different assessment needs in the SHL catalog. "
            f"{left.name}: {self._short_catalog_fact(left)} "
            f"{right.name}: {self._short_catalog_fact(right)} "
            "Use the first when that catalog description is closer to your role requirement; use the second when its catalog description better matches the trait or ability you need to measure."
        )
        recs = [
            Recommendation(name=left.name, url=left.url, test_type=left.test_type or "Unknown"),
            Recommendation(name=right.name, url=right.url, test_type=right.test_type or "Unknown"),
        ]
        return reply, recs, False

    def _find_mentioned_assessments(self, text: str) -> list[Assessment]:
        text_l = text.lower()
        found: list[Assessment] = []
        for item in self.catalog:
            name_l = item.name.lower()
            tokens = [t for t in re.split(r"[^a-zA-Z0-9+#.]+", name_l) if len(t) >= 2]
            if name_l in text_l or any(t in text_l for t in tokens if t in {"opq", "gsa", "java", "python", "sql"}):
                if item not in found:
                    found.append(item)
        return found[:4]

    def _short_catalog_fact(self, item: Assessment) -> str:
        fact = item.description or item.raw_text
        fact = " ".join(fact.split())
        if len(fact) > 240:
            fact = fact[:237].rsplit(" ", 1)[0] + "..."
        return fact or f"catalog type {item.test_type or 'Unknown'}."
