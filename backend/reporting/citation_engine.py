from typing import Any

from backend.schemas.research import SharedResearchContext


class CitationEngine:
    """
    Centralized Citation Engine resolving sources and formatting publication-quality references.
    """

    @staticmethod
    def generate_references(context: SharedResearchContext) -> list[dict[str, Any]]:
        """
        Extracts unique evidence references from the EvidenceStore and formats them as formal bibliography citations.
        """
        refs = []
        seen_urls = set()

        # Centralized evidence store extraction
        entries = (
            context.evidence_store.entries
            if hasattr(context, "evidence_store") and context.evidence_store
            else []
        )
        for entry in entries:
            ev = entry.evidence
            if not ev.url or ev.url in seen_urls:
                continue

            seen_urls.add(ev.url)
            # Format standard bibliography item
            formatted = f"[{len(refs) + 1}] {ev.source}. Available at: {ev.url}"
            refs.append(
                {
                    "index": len(refs) + 1,
                    "source": ev.source,
                    "url": ev.url,
                    "confidence": ev.confidence,
                    "quote": ev.quote,
                    "citation_text": formatted,
                    "section": entry.section,
                    "field_name": entry.field_name,
                }
            )

        return refs
