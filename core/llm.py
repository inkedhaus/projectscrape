"""LLM integration for AdSpy Marketing Suite."""

import json
import logging
from typing import Any

import openai

from .config import load_config

logger = logging.getLogger(__name__)


class LLMClient:
    """OpenAI LLM client for ad analysis."""

    def __init__(self):
        self.config = load_config()
        openai.api_key = self.config.openai_api_key
        self.model = self.config.openai_model

    def analyze_ad(self, ad_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze a single ad and extract insights."""
        prompt = f"""
        Analyze this Facebook ad and provide insights:

        Brand: {ad_data.get('brand', 'Unknown')}
        Headline: {ad_data.get('headline', '')}
        Body: {ad_data.get('body', '')}
        Call to Action: {ad_data.get('call_to_action', '')}

        Provide analysis in JSON format with these fields:
        - hook_analysis: What makes the hook compelling
        - angle: The marketing angle being used
        - pain_points: Pain points being addressed
        - benefits: Key benefits highlighted
        - emotion: Primary emotion being triggered
        - target_audience: Likely target demographic
        - effectiveness_score: Score 1-10 for estimated effectiveness
        - improvements: Suggestions for improvement
        """

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a marketing expert specializing in ad analysis. Provide detailed, actionable insights.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logger.error(f"Error analyzing ad: {e}")
            return {
                "hook_analysis": "Error in analysis",
                "angle": "Unknown",
                "pain_points": [],
                "benefits": [],
                "emotion": "Unknown",
                "target_audience": "Unknown",
                "effectiveness_score": 0,
                "improvements": [],
            }

    def generate_campaign_strategy(
        self, insights: list[dict[str, Any]], budget: float, objective: str
    ) -> dict[str, Any]:
        """Generate campaign strategy based on ad insights."""
        prompt = f"""
        Based on these ad insights, create a comprehensive campaign strategy:

        Budget: ${budget}/day
        Objective: {objective}

        Insights Summary:
        {json.dumps(insights, indent=2)}

        Generate a complete campaign strategy in JSON format with:
        - campaign_structure: Ad sets and targeting recommendations
        - creative_angles: Top 3 angles to test
        - audience_segments: Detailed audience targeting
        - budget_allocation: How to split budget across ad sets
        - testing_plan: A/B test recommendations
        - scaling_strategy: How to scale winning ads
        - expected_metrics: Predicted CTR, CPC, ROAS ranges
        """

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Facebook ads strategist with expertise in campaign planning and optimization.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=2000,
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logger.error(f"Error generating strategy: {e}")
            return {
                "error": f"Strategy generation failed: {str(e)}",
                "campaign_structure": [],
                "creative_angles": [],
                "audience_segments": [],
                "budget_allocation": {},
                "testing_plan": [],
                "scaling_strategy": {},
                "expected_metrics": {},
            }

    def extract_patterns(self, ads: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract common patterns from multiple ads."""
        headlines = [ad.get("headline", "") for ad in ads[:20]]
        bodies = [ad.get("body", "") for ad in ads[:20]]

        prompt = f"""
        Analyze these ad headlines and bodies to extract common patterns:

        Headlines:
        {json.dumps(headlines, indent=2)}

        Bodies:
        {json.dumps(bodies, indent=2)}

        Identify patterns in JSON format:
        - common_hooks: Most frequent opening lines/hooks
        - power_words: Words that appear frequently in successful ads
        - emotional_triggers: Common emotional appeals
        - structure_patterns: Common ad structure patterns
        - cta_patterns: Most used call-to-action phrases
        - length_analysis: Optimal headline and body length insights
        """

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a copywriting expert specializing in pattern recognition in advertising.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=1500,
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")
            return {
                "common_hooks": [],
                "power_words": [],
                "emotional_triggers": [],
                "structure_patterns": [],
                "cta_patterns": [],
                "length_analysis": {},
            }
