"""Ad analyzer with AI-powered insights."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from core.db import Database
from core.llm import LLMClient

logger = logging.getLogger(__name__)


class AdAnalyzer:
    """Analyze ads and extract insights using AI."""

    def __init__(self):
        self.llm_client = LLMClient()
        self.db = Database()

    def analyze_ads(self, ads: list[dict[str, Any]], max_workers: int = 5) -> list[dict[str, Any]]:
        """Analyze multiple ads concurrently."""
        results = []

        # Use ThreadPoolExecutor for concurrent analysis
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all analysis tasks
            future_to_ad = {executor.submit(self.analyze_single_ad, ad): ad for ad in ads}

            # Collect results as they complete
            total = len(ads)

            for completed, future in enumerate(as_completed(future_to_ad), 1):
                ad = future_to_ad[future]

                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        # Save analysis to database
                        self.db.save_analysis(
                            ad_id=ad.get("id", ""),
                            analysis_type="ai_analysis",
                            insights=result,
                            score=result.get("effectiveness_score", 0),
                        )

                    print(f"Analyzed {completed}/{total} ads", end="\r")

                except Exception as e:
                    logger.error(f"Error analyzing ad {ad.get('id', 'unknown')}: {e}")

        print(f"\nCompleted analysis of {len(results)} ads")
        return results

    def analyze_single_ad(self, ad: dict[str, Any]) -> dict[str, Any]:
        """Analyze a single ad using LLM."""
        try:
            analysis = self.llm_client.analyze_ad(ad)
            analysis["ad_id"] = ad.get("id", "")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing ad {ad.get('id', 'unknown')}: {e}")
            return {
                "ad_id": ad.get("id", ""),
                "hook_analysis": "Analysis failed",
                "angle": "Unknown",
                "pain_points": [],
                "benefits": [],
                "emotion": "Unknown",
                "target_audience": "Unknown",
                "effectiveness_score": 0,
                "improvements": ["Analysis failed due to error"],
                "error": str(e),
            }

    def extract_patterns(self, ads: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract common patterns from ads using LLM."""
        try:
            return self.llm_client.extract_patterns(ads)

        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")
            return {
                "common_hooks": [],
                "power_words": [],
                "emotional_triggers": [],
                "structure_patterns": [],
                "cta_patterns": [],
                "length_analysis": {},
                "error": str(e),
            }

    def get_top_performing_ads(
        self, ads: list[dict[str, Any]], limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get top performing ads based on analysis scores."""
        # Get analysis data from database
        analysis_data = {}
        for analysis in self.db.get_analysis():
            analysis_data[analysis["ad_id"]] = analysis

        # Score ads
        scored_ads = []
        for ad in ads:
            analysis = analysis_data.get(ad.get("id", ""))
            if analysis:
                try:
                    insights = analysis.get("insights", "{}")
                    if isinstance(insights, str):
                        import json

                        insights = json.loads(insights)

                    score = insights.get("effectiveness_score", 0)
                    ad_copy = ad.copy()
                    ad_copy["analysis_score"] = score
                    ad_copy["analysis"] = insights
                    scored_ads.append(ad_copy)
                except Exception as e:
                    logger.error(f"Error processing analysis for ad {ad.get('id')}: {e}")

        # Sort by score and return top performers
        scored_ads.sort(key=lambda x: x.get("analysis_score", 0), reverse=True)
        return scored_ads[:limit]

    def analyze_brand_performance(self, brand: str) -> dict[str, Any]:
        """Analyze performance of specific brand."""
        ads = self.db.get_ads(brand=brand)

        if not ads:
            return {"error": f"No ads found for brand: {brand}"}

        # Get analysis for brand ads
        brand_analysis = []
        for analysis in self.db.get_analysis():
            for ad in ads:
                if analysis["ad_id"] == ad.get("id"):
                    try:
                        insights = analysis.get("insights", "{}")
                        if isinstance(insights, str):
                            import json

                            insights = json.loads(insights)
                        brand_analysis.append(insights)
                    except Exception as e:
                        logger.error(f"Error processing analysis: {e}")

        if not brand_analysis:
            return {"error": f"No analysis data found for brand: {brand}"}

        # Calculate brand metrics
        effectiveness_scores = [a.get("effectiveness_score", 0) for a in brand_analysis]
        emotions = [a.get("emotion", "") for a in brand_analysis]
        angles = [a.get("angle", "") for a in brand_analysis]

        return {
            "brand": brand,
            "total_ads": len(ads),
            "analyzed_ads": len(brand_analysis),
            "avg_effectiveness": (
                sum(effectiveness_scores) / len(effectiveness_scores) if effectiveness_scores else 0
            ),
            "max_effectiveness": max(effectiveness_scores) if effectiveness_scores else 0,
            "min_effectiveness": min(effectiveness_scores) if effectiveness_scores else 0,
            "common_emotions": list(set(emotions)),
            "common_angles": list(set(angles)),
            "top_performing_ad": (
                max(
                    ads,
                    key=lambda x: next(
                        (
                            a.get("effectiveness_score", 0)
                            for a in brand_analysis
                            if a.get("ad_id") == x.get("id")
                        ),
                        0,
                    ),
                )
                if ads
                else None
            ),
        }
