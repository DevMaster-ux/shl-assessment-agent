from fastapi import FastAPI

from app.agent import ShlAgent
from app.catalog import load_catalog
from app.schemas import ChatRequest, ChatResponse

app = FastAPI(title="SHL Conversational Assessment Agent")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    agent = ShlAgent(load_catalog())
    reply, recommendations, end = agent.respond(request.messages)
    return ChatResponse(
        reply=reply,
        recommendations=recommendations,
        end_of_conversation=end,
    )
