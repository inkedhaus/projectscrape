"""Campaign strategy generation main module."""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from core.config import load_config
from core.llm import LLMClient


def load_insights_file(filepath: str) -> list[dict[str, Any]]:
    """Load insights from JSON file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        # Extract insights from different file formats
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if "top_ads" in data:
                # Extract analysis from top ads
                insights = []
                for ad in data["top_ads"]:
                    if "analysis" in ad:
                        insights.append(ad["analysis"])
                return insights
            if "patterns" in data:
                # Convert patterns to insights format
                return [data["patterns"]]
            return [data]

        return []

    except Exception as e:
        print(f"Error loading insights file {filepath}: {e}")
        return []


def save_campaign_structure(strategy: dict[str, Any], output_path: str):
    """Save campaign structure to JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(strategy, f, indent=2, ensure_ascii=False)
    print(f"Campaign structure saved to: {output_path}")


def save_campaign_markdown(strategy: dict[str, Any], output_path: str):
    """Save campaign strategy to Markdown file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Campaign Strategy\n\n")
        f.write(f"**Campaign Name:** {strategy.get('name', 'Untitled Campaign')}\n")
        f.write(f"**Daily Budget:** ${strategy.get('budget', 0)}\n")
        f.write(f"**Objective:** {strategy.get('objective', 'conversions')}\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Campaign Structure
        if strategy.get("campaign_structure"):
            f.write("## Campaign Structure\n\n")
            for i, adset in enumerate(strategy["campaign_structure"], 1):
                f.write(f"### Ad Set {i}: {adset.get('name', f'Ad Set {i}')}\n\n")
                f.write(f"**Budget:** ${adset.get('budget', 0)}/day\n")
                f.write(f"**Audience:** {adset.get('audience', 'N/A')}\n")
                f.write(f"**Placement:** {adset.get('placement', 'Automatic')}\n\n")

        # Creative Angles
        if strategy.get("creative_angles"):
            f.write("## Creative Angles to Test\n\n")
            for i, angle in enumerate(strategy["creative_angles"], 1):
                f.write(f"{i}. {angle}\n")
            f.write("\n")

        # Audience Segments
        if strategy.get("audience_segments"):
            f.write("## Audience Segments\n\n")
            for segment in strategy["audience_segments"]:
                f.write(f"**{segment.get('name', 'Segment')}**\n")
                f.write(f"- Description: {segment.get('description', 'N/A')}\n")
                f.write(f"- Size: {segment.get('size', 'N/A')}\n")
                f.write(f"- Interests: {', '.join(segment.get('interests', []))}\n\n")

        # Budget Allocation
        if strategy.get("budget_allocation"):
            f.write("## Budget Allocation\n\n")
            for adset, budget in strategy["budget_allocation"].items():
                f.write(f"- **{adset}:** ${budget}/day\n")
            f.write("\n")

        # Testing Plan
        if strategy.get("testing_plan"):
            f.write("## Testing Plan\n\n")
            for i, test in enumerate(strategy["testing_plan"], 1):
                f.write(f"### Test {i}: {test.get('name', f'Test {i}')}\n\n")
                f.write(f"**Hypothesis:** {test.get('hypothesis', 'N/A')}\n")
                f.write(f"**Variables:** {', '.join(test.get('variables', []))}\n")
                f.write(f"**Success Metric:** {test.get('success_metric', 'N/A')}\n\n")

        # Expected Metrics
        if strategy.get("expected_metrics"):
            f.write("## Expected Performance Metrics\n\n")
            metrics = strategy["expected_metrics"]
            f.write(f"- **CTR:** {metrics.get('ctr', 'N/A')}%\n")
            f.write(f"- **CPC:** ${metrics.get('cpc', 'N/A')}\n")
            f.write(f"- **CPM:** ${metrics.get('cpm', 'N/A')}\n")
            f.write(f"- **ROAS:** {metrics.get('roas', 'N/A')}:1\n\n")

        # Scaling Strategy
        if strategy.get("scaling_strategy"):
            f.write("## Scaling Strategy\n\n")
            scaling = strategy["scaling_strategy"]
            f.write(f"**Criteria for Scaling:** {scaling.get('criteria', 'N/A')}\n")
            f.write(f"**Scaling Method:** {scaling.get('method', 'N/A')}\n")
            f.write(f"**Budget Increases:** {scaling.get('budget_increases', 'N/A')}\n\n")

    print(f"Campaign markdown saved to: {output_path}")


def main():
    """Main entry point for campaign strategy generation."""
    parser = argparse.ArgumentParser(description="Campaign Strategy Generator")
    parser.add_argument("--insights-file", help="Path to insights JSON file")
    parser.add_argument("--budget", type=float, default=100, help="Daily budget")
    parser.add_argument("--objective", default="conversions", help="Campaign objective")
    parser.add_argument("--campaign-name", default="AI Generated Campaign", help="Campaign name")
    parser.add_argument("--output-dir", default="data/reports", help="Output directory")

    args = parser.parse_args()
    config = load_config()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating campaign strategy...")
    print(f"Budget: ${args.budget}/day")
    print(f"Objective: {args.objective}")
    print(f"Campaign Name: {args.campaign_name}")

    # Load insights
    insights = []
    if args.insights_file:
        if Path(args.insights_file).exists():
            insights = load_insights_file(args.insights_file)
            print(f"Loaded {len(insights)} insights from {args.insights_file}")
        else:
            print(f"Insights file not found: {args.insights_file}")
    else:
        # Look for latest insights file
        reports_dir = Path(config.reports_dir)
        if reports_dir.exists():
            insights_files = list(reports_dir.glob("insights_*.json"))
            if insights_files:
                latest_file = max(insights_files, key=lambda x: x.stat().st_mtime)
                insights = load_insights_file(str(latest_file))
                print(f"Auto-loaded {len(insights)} insights from {latest_file}")

    if not insights:
        print("No insights available. Generating basic strategy...")
        insights = [{"note": "No specific ad insights available"}]

    # Generate strategy
    try:
        llm_client = LLMClient()
        print("Generating strategy with AI...")

        strategy = llm_client.generate_campaign_strategy(insights, args.budget, args.objective)

        # Add metadata
        strategy["name"] = args.campaign_name
        strategy["budget"] = args.budget
        strategy["objective"] = args.objective
        strategy["generated_at"] = datetime.now().isoformat()

        # Save outputs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON strategy file
        json_path = output_dir / f"campaign_strategy_{timestamp}.json"
        save_campaign_structure(strategy, str(json_path))

        # Markdown strategy file
        md_path = output_dir / f"campaign_strategy_{timestamp}.md"
        save_campaign_markdown(strategy, str(md_path))

        # Print summary
        print("\n=== Campaign Strategy Generated ===")
        print(f"Campaign: {strategy.get('name')}")
        print(f"Budget: ${strategy.get('budget')}/day")

        if strategy.get("creative_angles"):
            print(f"\nTop creative angles ({len(strategy['creative_angles'])}):")
            for angle in strategy["creative_angles"][:3]:
                print(f"  • {angle}")

        if strategy.get("audience_segments"):
            print(f"\nAudience segments ({len(strategy['audience_segments'])}):")
            for segment in strategy["audience_segments"][:3]:
                print(f"  • {segment.get('name', 'Unnamed segment')}")

        if strategy.get("expected_metrics"):
            metrics = strategy["expected_metrics"]
            print("\nExpected performance:")
            if "ctr" in metrics:
                print(f"  • CTR: {metrics['ctr']}%")
            if "roas" in metrics:
                print(f"  • ROAS: {metrics['roas']}:1")

        print(f"\nStrategy files saved to {output_dir}")

    except Exception as e:
        print(f"Error generating strategy: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
