from fastapi import FastAPI
from pydantic import BaseModel

from core.cortex.dispatch import CortexDispatcher

app = FastAPI()

dispatcher = CortexDispatcher()


class ChatRequest(BaseModel):
    text: str


@app.get("/ping")
def ping():
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest):
    return await dispatcher.dispatch(req.text)
