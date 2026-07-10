from backend.schemas.research import (
    CompanyProfile,
    CompetitorAnalysis,
    NewsSummary,
    WebsiteAnalysis,
)

# Deterministic source priority map
SOURCE_CONFIDENCE_POLICY = {
    "Official Website": 1.00,
    "Annual Report": 0.98,
    "Investor Relations": 0.97,
    "Government Filing": 0.96,
    "Official Blog": 0.95,
    "Official Newsroom": 0.94,
    "Google News RSS": 0.88,
    "Wikipedia": 0.80,
    "Multi-source Verification": 0.70,
    "LLM Inference": 0.40,
    "Not Available": 0.00,
}


def get_confidence_from_source(source_text: str, domain: str = "") -> float:
    """
    Evaluates the priority of the source text descriptor, returning a deterministic confidence score.
    """
    if not source_text or source_text.strip() == "Not Available":
        return 0.0

    s_lower = source_text.lower()

    # 1. Match official domain string or descriptor (highest priority)
    if "official website" in s_lower or (domain and domain.lower() in s_lower):
        if "blog" in s_lower:
            return SOURCE_CONFIDENCE_POLICY["Official Blog"]
        if "newsroom" in s_lower or "press" in s_lower:
            return SOURCE_CONFIDENCE_POLICY["Official Newsroom"]
        if "investor" in s_lower or "ir." in s_lower:
            return SOURCE_CONFIDENCE_POLICY["Investor Relations"]
        return SOURCE_CONFIDENCE_POLICY["Official Website"]

    # 2. Check standard source priority match keys
    if "annual report" in s_lower or "10-k" in s_lower:
        return SOURCE_CONFIDENCE_POLICY["Annual Report"]
    if "investor relations" in s_lower or "ir.stripe" in s_lower:
        return SOURCE_CONFIDENCE_POLICY["Investor Relations"]
    if "sec filing" in s_lower or "government filing" in s_lower or "sec.gov" in s_lower:
        return SOURCE_CONFIDENCE_POLICY["Government Filing"]
    if "official blog" in s_lower:
        return SOURCE_CONFIDENCE_POLICY["Official Blog"]
    if "newsroom" in s_lower or "press release" in s_lower:
        return SOURCE_CONFIDENCE_POLICY["Official Newsroom"]
    if "google news" in s_lower or "news.google" in s_lower or "rss" in s_lower:
        return SOURCE_CONFIDENCE_POLICY["Google News RSS"]
    if "wikipedia" in s_lower:
        return SOURCE_CONFIDENCE_POLICY["Wikipedia"]
    if "multi-source" in s_lower or "verified" in s_lower:
        return SOURCE_CONFIDENCE_POLICY["Multi-source Verification"]
    if "llm" in s_lower or "inference" in s_lower or "reasoning" in s_lower:
        return SOURCE_CONFIDENCE_POLICY["LLM Inference"]

    # Fallback default if it contains url or text, but not explicitly matched
    return 0.60


def evaluate_report_quality(
    profile: CompanyProfile,
    web_analysis: WebsiteAnalysis,
    news_summary: NewsSummary,
    competitors_data: CompetitorAnalysis,
) -> float:
    """
    Averages the confidence scores across all core factual fields to calculate an overall quality score.
    """
    scores = []

    # CompanyProfile fields
    scores.append(profile.name.confidence)
    scores.append(profile.domain.confidence)
    scores.append(profile.industry.confidence)
    scores.append(profile.description.confidence)
    scores.append(profile.hq_location.confidence)
    scores.append(profile.founded_year.confidence)
    scores.append(profile.key_leadership.confidence)

    # WebsiteAnalysis fields
    scores.append(web_analysis.meta_title.confidence)
    scores.append(web_analysis.meta_description.confidence)
    scores.append(web_analysis.technologies_found.confidence)
    scores.append(web_analysis.extracted_topics.confidence)

    # NewsSummary fields
    scores.append(news_summary.key_corporate_events.confidence)
    scores.append(news_summary.sentiment_summary.confidence)

    # CompetitorAnalysis fields
    scores.append(competitors_data.market_positioning.confidence)

    valid_scores = [s for s in scores if s is not None]
    if not valid_scores:
        return 0.0
    return round(sum(valid_scores) / len(valid_scores), 2)
