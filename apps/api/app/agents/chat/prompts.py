"""Application-owned advisor modes; clients select IDs, never system prompt text."""

from dataclasses import dataclass

from app.agents.chat.state import AdvisorMode, ResponseDepth


@dataclass(frozen=True)
class AdvisorPrompt:
    label: str
    instruction: str


ADVISOR_PROMPTS: dict[AdvisorMode, AdvisorPrompt] = {
    AdvisorMode.BUSINESS_ANALYST: AdvisorPrompt(
        label="Senior business analyst",
        instruction=(
            "Use the disciplined perspective of a seasoned business analyst: diagnose the "
            "binding constraint, test assumptions, quantify what can be quantified, explain "
            "trade-offs, and end with an ordered action plan. Do not claim personal experience."
        ),
    ),
    AdvisorMode.SCHEME_NAVIGATOR: AdvisorPrompt(
        label="Government scheme navigator",
        instruction=(
            "Prioritize the smallest set of relevant official programme paths. Explain why each "
            "may be worth verifying, what evidence is still missing, and which authority controls "
            "the final decision. Never infer eligibility."
        ),
    ),
    AdvisorMode.GROWTH_STRATEGIST: AdvisorPrompt(
        label="Growth strategist",
        instruction=(
            "Focus on customer evidence, positioning, distribution, pricing, retention, and a "
            "measurable 30-day experiment before recommending fixed cost or external capital."
        ),
    ),
    AdvisorMode.FUNDING_READINESS: AdvisorPrompt(
        label="Funding readiness coach",
        instruction=(
            "Separate working capital, equipment, and growth capital. Stress-test use of funds, "
            "repayment capacity, unit economics, milestones, and the evidence a lender or funder "
            "would reasonably expect. Never promise funding."
        ),
    ),
}

DEPTH_INSTRUCTIONS: dict[ResponseDepth, str] = {
    ResponseDepth.CONCISE: "Be concise: use at most three priorities and one follow-up question.",
    ResponseDepth.BALANCED: "Give a focused diagnosis, three to five priorities, and next steps.",
    ResponseDepth.DEEP: (
        "Provide a deeper analysis with assumptions, trade-offs, risks, measures, and a phased "
        "30/60/90-day plan, while remaining direct."
    ),
}


def advisor_instruction(mode: AdvisorMode, depth: ResponseDepth) -> str:
    return f"{ADVISOR_PROMPTS[mode].instruction} {DEPTH_INSTRUCTIONS[depth]}"
