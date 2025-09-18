"""AI-powered ad analysis main module."""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from core.db import Database
from core.llm import LLMClient

from .analyzer import AdAnalyzer


def save_insights_report(insights: dict[str, Any], output_path: str):
    """Save insights to JSON report."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)
    print(f"Insights report saved to: {output_path}")


def save_markdown_report(insights: dict[str, Any], output_path: str):
    """Save insights to Markdown report."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Ad Analysis Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        if "summary" in insights:
            f.write("## Summary\n\n")
            f.write(f"- Total ads analyzed: {insights['summary'].get('total_ads', 0)}\n")
            f.write(
                f"- Average effectiveness score: {insights['summary'].get('avg_effectiveness', 0):.2f}\n"
            )
            f.write(f"- Top performing brand: {insights['summary'].get('top_brand', 'N/A')}\n\n")

        if "patterns" in insights:
            patterns = insights["patterns"]
            f.write("## Common Patterns\n\n")

            if patterns.get("common_hooks"):
                f.write("### Top Hooks\n\n")
                for hook in patterns["common_hooks"][:5]:
                    f.write(f"- {hook}\n")
                f.write("\n")

            if patterns.get("power_words"):
                f.write("### Power Words\n\n")
                for word in patterns["power_words"][:10]:
                    f.write(f"- {word}\n")
                f.write("\n")

            if patterns.get("emotional_triggers"):
                f.write("### Emotional Triggers\n\n")
                for trigger in patterns["emotional_triggers"][:5]:
                    f.write(f"- {trigger}\n")
                f.write("\n")

        if "top_ads" in insights:
            f.write("## Top Performing Ads\n\n")
            for i, ad in enumerate(insights["top_ads"][:5], 1):
                f.write(f"### #{i} - {ad.get('brand', 'Unknown Brand')}\n\n")
                f.write(f"**Headline:** {ad.get('headline', 'N/A')}\n\n")
                f.write(f"**Body:** {ad.get('body', 'N/A')[:200]}...\n\n")
                if "analysis" in ad:
                    analysis = ad["analysis"]
                    f.write(
                        f"**Effectiveness Score:** {analysis.get('effectiveness_score', 0)}/10\n\n"
                    )
                    f.write(f"**Key Insight:** {analysis.get('hook_analysis', 'N/A')}\n\n")

        if "strategy" in insights:
            strategy = insights["strategy"]
            f.write("## Recommended Strategy\n\n")

            if strategy.get("creative_angles"):
                f.write("### Top Creative Angles\n\n")
                for angle in strategy["creative_angles"][:3]:
                    f.write(f"- {angle}\n")
                f.write("\n")

            if strategy.get("audience_segments"):
                f.write("### Audience Segments\n\n")
                for segment in strategy["audience_segments"][:3]:
                    f.write(
                        f"- **{segment.get('name', 'Segment')}**: {segment.get('description', 'N/A')}\n"
                    )
                f.write("\n")

    print(f"Markdown report saved to: {output_path}")


def main():
    """Main entry point for ad analysis."""
    parser = argparse.ArgumentParser(description="AI-Powered Ad Analysis")
    parser.add_argument("--limit", type=int, default=150, help="Number of ads to analyze")
    parser.add_argument("--brand", help="Filter by specific brand")
    parser.add_argument("--strategy", action="store_true", help="Generate campaign strategy")
    parser.add_argument(
        "--budget", type=float, default=100, help="Daily budget for strategy generation"
    )
    parser.add_argument("--objective", default="conversions", help="Campaign objective")
    parser.add_argument("--output-dir", default="data/reports", help="Output directory for reports")

    args = parser.parse_args()
    db = Database()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Starting ad analysis...")
    print(f"Analyzing up to {args.limit} ads")
    if args.brand:
        print(f"Filtering by brand: {args.brand}")

    # Get ads from database
    ads = db.get_ads(limit=args.limit, brand=args.brand)

    if not ads:
        print("No ads found in database. Run the scraper first.")
        return

    print(f"Found {len(ads)} ads in database")

    # Initialize analyzer
    analyzer = AdAnalyzer()

    try:
        # Analyze ads
        print("Analyzing ads with AI...")
        analysis_results = analyzer.analyze_ads(ads)

        print(f"Analyzed {len(analysis_results)} ads")

        # Extract patterns
        print("Extracting common patterns...")
        patterns = analyzer.extract_patterns(ads)

        # Generate insights
        insights = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_ads": len(analysis_results),
                "avg_effectiveness": (
                    sum(r.get("effectiveness_score", 0) for r in analysis_results)
                    / len(analysis_results)
                    if analysis_results
                    else 0
                ),
                "top_brand": (
                    max(
                        set(ad.get("brand", "") for ad in ads),
                        key=lambda x: sum(1 for ad in ads if ad.get("brand") == x),
                    )
                    if ads
                    else "N/A"
                ),
            },
            "patterns": patterns,
            "top_ads": [],
        }

        # Get top performing ads
        ads_with_analysis = []
        for ad in ads:
            for analysis in analysis_results:
                if analysis.get("ad_id") == ad.get("id"):
                    ad_copy = ad.copy()
                    ad_copy["analysis"] = analysis
                    ads_with_analysis.append(ad_copy)
                    break

        # Sort by effectiveness score
        ads_with_analysis.sort(
            key=lambda x: x.get("analysis", {}).get("effectiveness_score", 0), reverse=True
        )
        insights["top_ads"] = ads_with_analysis[:10]

        # Generate strategy if requested
        if args.strategy:
            print("Generating campaign strategy...")
            llm_client = LLMClient()
            strategy = llm_client.generate_campaign_strategy(
                analysis_results, args.budget, args.objective
            )
            insights["strategy"] = strategy

        # Save reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON report
        json_path = output_dir / f"insights_{timestamp}.json"
        save_insights_report(insights, str(json_path))

        # Markdown report
        md_path = output_dir / f"analysis_report_{timestamp}.md"
        save_markdown_report(insights, str(md_path))

        # Print summary
        print("\n=== Analysis Summary ===")
        print(f"Total ads analyzed: {insights['summary']['total_ads']}")
        print(f"Average effectiveness score: {insights['summary']['avg_effectiveness']:.2f}/10")
        print(f"Top performing brand: {insights['summary']['top_brand']}")

        if patterns.get("common_hooks"):
            print("\nTop hooks found:")
            for hook in patterns["common_hooks"][:3]:
                print(f"  • {hook}")

        if args.strategy and "strategy" in insights:
            print(f"\nStrategy generated for ${args.budget}/day budget")
            if insights["strategy"].get("creative_angles"):
                print("Top creative angles:")
                for angle in insights["strategy"]["creative_angles"][:3]:
                    print(f"  • {angle}")

        print(f"\nReports saved to {output_dir}")

    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
