import asyncio
import json
import logging

import openai
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AdHook(BaseModel):
    type: str  # problem, benefit, curiosity, fear, social_proof
    text: str
    strength: int  # 1-10


class AdStructure(BaseModel):
    hook: AdHook
    body_points: list[str]
    cta: str
    urgency_elements: list[str]
    social_proof: list[str]


class AIAdAnalyzer:
    def __init__(self, openai_key: str):
        self.client = openai.OpenAI(api_key=openai_key)
        self.model = "gpt-4-1106-preview"

    async def analyze_ad(self, ad_data: dict) -> dict:
        """Deep analysis of a single ad"""

        try:
            prompt = self._build_analysis_prompt(ad_data)

            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            analysis = json.loads(response.choices[0].message.content)

            # Add risk assessment
            analysis["risks"] = self._assess_risks(ad_data, analysis)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing ad: {e}")
            return {"error": str(e)}

    async def batch_analyze(self, ads: list[dict], max_concurrent: int = 5) -> list[dict]:
        """Analyze multiple ads concurrently"""

        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(ad):
            async with semaphore:
                return await self.analyze_ad(ad)

        tasks = [analyze_with_semaphore(ad) for ad in ads]
        return await asyncio.gather(*tasks)

    def _get_system_prompt(self) -> str:
        return """You are an expert marketing analyst specializing in competitor ad analysis.
        Your job is to analyze ads and extract key insights about their marketing strategy.

        Analyze the ad for:
        1. Hook type and strength (problem, benefit, curiosity, fear, social proof)
        2. Psychological triggers used
        3. Target audience indicators
        4. Emotional tone and messaging
        5. Call-to-action effectiveness
        6. Overall effectiveness score (1-10)

        Return your analysis as a JSON object with clear, actionable insights."""

    def _build_analysis_prompt(self, ad_data: dict) -> str:
        return f"""
        Analyze this {ad_data.get('platform', 'unknown')} ad:

        Brand: {ad_data.get('brand', 'Unknown')}
        Copy: {ad_data.get('copy', '')}
        CTA: {ad_data.get('cta', '')}
        Platform: {ad_data.get('platform', 'unknown')}

        Provide a comprehensive analysis including:
        - Hook identification and strength rating
        - Psychological triggers used
        - Target audience profile
        - Emotional appeal analysis
        - CTA effectiveness
        - Overall effectiveness score (1-10)
        - Improvement suggestions
        """

    def _assess_risks(self, ad_data: dict, analysis: dict) -> list[str]:
        """Assess potential risks in the ad copy"""

        risks = []
        copy = ad_data.get("copy", "").lower()

        # Check for potentially risky claims
        risky_phrases = [
            "guaranteed",
            "miracle",
            "instant",
            "overnight",
            "secret",
            "doctors hate",
            "weird trick",
            "lose weight fast",
        ]

        for phrase in risky_phrases:
            if phrase in copy:
                risks.append(f"Potentially misleading claim: '{phrase}'")

        # Check for compliance issues
        if "medical" in analysis.get("category", "").lower():
            risks.append("Medical claims may require FDA compliance")

        if "financial" in analysis.get("category", "").lower():
            risks.append("Financial claims may require regulatory compliance")

        return risks

    async def generate_insights_report(self, analyses: list[dict]) -> dict:
        """Generate aggregated insights from multiple ad analyses"""

        if not analyses:
            return {"error": "No analyses provided"}

        # Aggregate data
        total_ads = len(analyses)
        avg_effectiveness = sum(a.get("effectiveness_score", 0) for a in analyses) / total_ads

        # Most common hooks
        hook_types = [a.get("hook", {}).get("type") for a in analyses if a.get("hook")]
        hook_counts = {}
        for hook in hook_types:
            if hook:
                hook_counts[hook] = hook_counts.get(hook, 0) + 1

        # Most common psychological triggers
        all_triggers = []
        for analysis in analyses:
            triggers = analysis.get("psychological_triggers", [])
            all_triggers.extend(triggers)

        trigger_counts = {}
        for trigger in all_triggers:
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1

        return {
            "summary": {
                "total_ads_analyzed": total_ads,
                "average_effectiveness": round(avg_effectiveness, 2),
                "most_common_hooks": sorted(hook_counts.items(), key=lambda x: x[1], reverse=True)[
                    :5
                ],
                "most_common_triggers": sorted(
                    trigger_counts.items(), key=lambda x: x[1], reverse=True
                )[:10],
            },
            "recommendations": self._generate_recommendations(analyses),
            "top_performing_ads": sorted(
                [a for a in analyses if a.get("effectiveness_score")],
                key=lambda x: x.get("effectiveness_score", 0),
                reverse=True,
            )[:5],
        }

    def _generate_recommendations(self, analyses: list[dict]) -> list[str]:
        """Generate strategic recommendations based on analysis"""

        recommendations = []

        # Effectiveness analysis
        high_performing = [a for a in analyses if a.get("effectiveness_score", 0) >= 8]
        if high_performing:
            recommendations.append(
                f"Focus on high-performing patterns found in {len(high_performing)} top ads"
            )

        # Hook analysis
        hook_types = [a.get("hook", {}).get("type") for a in analyses if a.get("hook")]
        if hook_types:
            most_common_hook = max(set(hook_types), key=hook_types.count)
            recommendations.append(
                f"Consider using more '{most_common_hook}' hooks as they appear frequently in competitor ads"
            )

        # Risk analysis
        risky_ads = [a for a in analyses if a.get("risks")]
        if len(risky_ads) > len(analyses) * 0.3:  # More than 30% have risks
            recommendations.append(
                "Many competitor ads contain potential compliance risks - opportunity for cleaner messaging"
            )

        return recommendations
