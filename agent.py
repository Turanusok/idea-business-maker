import os
import json
from typing import TypedDict, Optional
from dotenv import load_dotenv
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from tavily import TavilyClient

load_dotenv()


class AgentState(TypedDict):
    raw_idea: str
    needs_clarification: bool
    clarifying_question: Optional[str]
    idea_summary: Optional[str]
    market_research: Optional[str]
    cost_estimate: Optional[str]
    roadmap: Optional[str]
    final_report: Optional[str]
    clarify_rounds: int


class ClarifyResult(BaseModel):
    needs_clarification: bool
    question_or_summary: str


llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0.4,
)
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("\n", 1)[0]
    return json.loads(text)


def clarify_idea(state: AgentState) -> AgentState:
    if state.get("clarify_rounds", 0) >= 1:
        return {**state, "needs_clarification": False, "idea_summary": state["raw_idea"]}

    prompt = f"""A user gave this business idea: "{state['raw_idea']}"

Decide if it's specific enough to research. If not, set needs_clarification=True
and put a follow-up question in question_or_summary. If yes, set
needs_clarification=False and put a clean one-sentence summary in question_or_summary.

Return your answer as a JSON object with keys "needs_clarification" (boolean) and "question_or_summary" (string). Return ONLY the JSON object, nothing else, no markdown formatting."""

    response = llm.invoke(prompt).content.strip()
    result = _extract_json(response)

    if result.get("needs_clarification"):
        return {**state, "needs_clarification": True, "clarifying_question": result.get("question_or_summary", "")}
    else:
        return {**state, "needs_clarification": False, "idea_summary": result.get("question_or_summary", "")}


def research_market(state: AgentState) -> AgentState:
    idea = state["idea_summary"]

    queries = [
        f"{idea} competitors existing businesses",
        f"{idea} startup cost how much money needed",
    ]

    findings = []
    for q in queries:
        res = tavily.search(query=q, max_results=3)
        for r in res.get("results", []):
            findings.append(f"- {r['title']}: {r['content'][:300]}")

    raw_text = "\n".join(findings)

    prompt = f"""Idea: {idea}

Search findings:
{raw_text}

Summarize into a short market snapshot (3-5 sentences): competitors, market
landscape, any cost signals."""

    summary = llm.invoke(prompt).content.strip()
    return {**state, "market_research": summary}


def estimate_costs(state: AgentState) -> AgentState:
    prompt = f"""Idea: {state['idea_summary']}

Market research: {state['market_research']}

Give a realistic startup cost breakdown:
- One-time costs (with $ ranges)
- Monthly recurring costs (with $ ranges)
- Total capital needed to launch

Keep numbers grounded in the research above, not generic guesses."""

    estimate = llm.invoke(prompt).content.strip()
    return {**state, "cost_estimate": estimate}


def build_roadmap(state: AgentState) -> AgentState:
    prompt = f"""Idea: {state['idea_summary']}

Market research: {state['market_research']}
Cost estimate: {state['cost_estimate']}

Write a phased roadmap with three sections: "Week 1", "Month 1", "Month 3".
Each section should have 3-5 concrete, specific action items — not vague
advice like "do market research," say exactly what to do.
"""

    roadmap = llm.invoke(prompt).content.strip()
    return {**state, "roadmap": roadmap}


def format_output(state: AgentState) -> AgentState:
    report = f"""# {state['idea_summary']}

## Market Snapshot
{state['market_research']}

## Estimated Costs
{state['cost_estimate']}

## Roadmap
{state['roadmap']}
"""
    return {**state, "final_report": report}


def route_after_clarify(state: AgentState) -> str:
    return "end_for_clarification" if state["needs_clarification"] else "research_market"


graph = StateGraph(AgentState)

graph.add_node("clarify_idea", clarify_idea)
graph.add_node("research_market", research_market)
graph.add_node("estimate_costs", estimate_costs)
graph.add_node("build_roadmap", build_roadmap)
graph.add_node("format_output", format_output)

graph.set_entry_point("clarify_idea")

graph.add_conditional_edges(
    "clarify_idea",
    route_after_clarify,
    {
        "end_for_clarification": END,
        "research_market": "research_market",
    },
)

graph.add_edge("research_market", "estimate_costs")
graph.add_edge("estimate_costs", "build_roadmap")
graph.add_edge("build_roadmap", "format_output")
graph.add_edge("format_output", END)

agent_graph = graph.compile()

if __name__ == "__main__":
    a = input("Enter a business idea: ")
    result = agent_graph.invoke({"raw_idea": a, "needs_clarification": False, "clarifying_question": None, "idea_summary": None, "market_research": None, "cost_estimate": None, "roadmap": None, "final_report": None, "clarify_rounds": 0})

    if result["needs_clarification"]:
        print("Need more info:", result["clarifying_question"])
    else:
        print(result["final_report"])