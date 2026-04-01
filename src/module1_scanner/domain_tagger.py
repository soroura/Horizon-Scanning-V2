"""
Domain keyword tagger — assigns domain labels to raw scan items.
Constitution Principle II: keyword banks loaded from config/domains.yaml.
"""
from __future__ import annotations

from pathlib import Path

from src.config_loader import DomainDefinition, load_domains


class DomainTagger:
    """
    Tags items with domain codes by matching keywords against title + summary.
    Items with no domain match are dropped (not emitted to scorer).
    """

    def __init__(self, domains: dict[str, DomainDefinition] | None = None):
        if domains is None:
            domains = load_domains()
        # Pre-lowercase all keywords for fast matching
        self._domains: dict[str, list[str]] = {
            code: [kw.lower() for kw in defn.keywords]
            for code, defn in domains.items()
        }

    def tag(self, title: str, summary: str) -> tuple[list[str], list[str]]:
        """
        Returns (domain_list, matched_keywords_list).
        domain_list is empty if no keywords matched — caller should drop the item.
        """
        haystack = (title + " " + summary).lower()
        matched_domains: list[str] = []
        matched_keywords: list[str] = []

        for domain_code, keywords in self._domains.items():
            hits = [kw for kw in keywords if kw in haystack]
            if hits:
                matched_domains.append(domain_code)
                matched_keywords.extend(hits[:5])  # cap per-domain for brevity

        # Deduplicate matched keywords
        seen: set[str] = set()
        deduped: list[str] = []
        for kw in matched_keywords:
            if kw not in seen:
                seen.add(kw)
                deduped.append(kw)

        return matched_domains, deduped

    def tag_item(self, raw: dict) -> dict | None:
        """
        Add domains and keywords_matched to a raw item dict.
        Returns None if no domains matched (item should be dropped).
        """
        domains, keywords = self.tag(
            raw.get("title", ""),
            raw.get("summary", ""),
        )
        if not domains:
            return None
        return {**raw, "domains": domains, "keywords_matched": keywords}
