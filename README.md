# Idea → Business Maker

A web app that turns a business idea into market research, startup cost estimates, and a simple roadmap.

Built for the Hack Club Stardance Challenge.

## How it works

1. Describe an idea, target customer, and location.
2. The agent asks follow-up questions if needed.
3. It researches competitors and market signals.
4. It returns costs and next steps.

## Stack

- Python + FastAPI
- LangGraph
- DeepSeek Chat API
- Tavily search
- HTML, CSS, JavaScript
- Docker + Caddy

## Run locally

Install dependencies:

```bash
pip install -r requirements.txt

uvicorn server:app --reload

