import argparse
import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

from src.services.ai.fixture_loader import load_fixture_state
from src.services.ai.graph import build_graph, run_review

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


async def main(fixture_name: str) -> None:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    fixture_dir = FIXTURES_DIR / fixture_name
    if not fixture_dir.is_dir():
        available = ", ".join(p.name for p in FIXTURES_DIR.iterdir() if p.is_dir())
        raise SystemExit(f"Unknown fixture '{fixture_name}'. Available: {available}")

    state = load_fixture_state(fixture_dir)
    graph = build_graph()
    result = await run_review(graph, state)

    print(f"\n=== Plan ===\n{result['plan'].model_dump_json(indent=2) if result.get('plan') else None}")
    print(f"\n=== Specialists run ===\n{result['specialists_run']}")
    print(f"\n=== Specialists failed ===\n{result['specialists_failed']}")
    print(f"\n=== Raw findings ({len(result['findings'])}) ===")
    for finding in result["findings"]:
        print(json.dumps(finding.model_dump(mode="json"), indent=2))
    print(f"\n=== Final report ({len(result['final_report'] or [])}) ===")
    for finding in result["final_report"] or []:
        print(json.dumps(finding.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the PR Auditor LangGraph review against a local fixture.")
    parser.add_argument("--fixture", required=True, help="Fixture directory name under tests/fixtures/")
    args = parser.parse_args()
    asyncio.run(main(args.fixture))
