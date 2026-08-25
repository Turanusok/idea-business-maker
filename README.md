# Idea → Business Maker

An AI agent that turns a raw business idea into a market snapshot, realistic startup cost estimate, and a phased execution roadmap.

Built for the [Hack Club Stardance Challenge](https://stardance.hackclub.com).

## What it does

You describe a business idea in plain language. The agent:

1. **Clarifies** — asks a follow-up question if your idea needs more detail (target customers, location, pricing model, etc.)
2. **Researches** — searches the web for real competitors and cost signals using Tavily
3. **Estimates costs** — breaks down one-time and recurring costs grounded in the research, not generic guesses
4. **Builds a roadmap** — a concrete Week 1 / Month 1 / Month 3 action plan

## Stack

- **Agent**: [LangGraph](https://www.langchain.com/langgraph) state machine (`agent.py`)
- **LLM**: DeepSeek Chat via OpenAI-compatible API
- **Search**: [Tavily](https://tavily.com) for live market research
- **Backend**: FastAPI (`server.py`)
- **Frontend**: Vanilla HTML/CSS/JS (`static/index.html`)
- **Deployment**: Docker, reverse-proxied with Caddy

## Running locally

```bash
pip install -r requirements.txt
```


Then run:
```bash
uvicorn server:app --reload
```

Visit `http://localhost:8000`.

## AI usage

Used Claude (Anthropic) as a coding tutor throughout development — explained LangGraph concepts, reviewed code, and helped debug environment/deployment issues. The core agent logic and application code were written by the author.

## Author

Built by [@Turanusok](https://github.com/Turanusok)