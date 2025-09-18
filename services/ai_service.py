from __future__ import annotations

from models import AIDailyBrief, AIExplainErrorRequest, AINextStepRequest, AIResponse


def explain_error(_: str, __: AIExplainErrorRequest) -> AIResponse:
    return AIResponse(
        message="This is a stubbed explanation. Integrate with the AI backend later.",
        recommendations=[
            "Review the stack trace for obvious misconfigurations.",
            "Consult project documentation for relevant troubleshooting steps.",
        ],
    )


def next_step(_: str, __: AINextStepRequest) -> AIResponse:
    return AIResponse(
        message="Stubbed recommendation for the next step in your workflow.",
        recommendations=[
            "Open a draft PR summarizing today's work.",
            "Queue integration tests before merging.",
        ],
    )


def daily_brief(_: str) -> AIDailyBrief:
    return AIDailyBrief(
        summary="Daily brief is currently stubbed.",
        highlights=[
            "No new alerts overnight.",
            "Two pull requests are awaiting review.",
            "CI pipeline succeeded on the latest commit.",
        ],
    )
