from src.schemas.state import ReviewState

ALL_SPECIALISTS = ["security", "style", "test_coverage", "perf"]


def route_to_specialists(state: ReviewState) -> list[str]:
    plan = state.get("plan")
    if plan is None:
        return []
    active = {agent.value for agent in plan.activate}
    return [name for name in ALL_SPECIALISTS if name in active]
