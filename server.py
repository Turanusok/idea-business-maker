from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional

from agent import agent_graph

app = FastAPI(title="Idea Business Maker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    idea: str
    history: Optional[List[str]] = []


class ChatResponse(BaseModel):
    needs_clarification: bool
    message: str


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        combined_idea = req.idea
        if req.history:
            qa_text = "\n".join(req.history)
            combined_idea = f"{req.idea}\n\nClarifications so far:\n{qa_text}"

        result = agent_graph.invoke({
            "raw_idea": combined_idea,
            "needs_clarification": False,
            "clarifying_question": None,
            "idea_summary": None,
            "market_research": None,
            "cost_estimate": None,
            "roadmap": None,
            "final_report": None,
            "clarify_rounds": len(req.history),
        })

        if result["needs_clarification"]:
            return ChatResponse(needs_clarification=True, message=result["clarifying_question"])
        return ChatResponse(needs_clarification=False, message=result["final_report"])
    except Exception as e:
        return ChatResponse(needs_clarification=False, message=f"Error: {e}")


@app.get("/")
def serve_index():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
