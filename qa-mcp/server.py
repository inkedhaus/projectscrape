import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

APP_NAME = "QA MCP"
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")

app = FastAPI(title=APP_NAME, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "message": f"{APP_NAME} running", "version": APP_VERSION}


@app.get("/health")
def health():
    return {"ok": True}


class EchoIn(BaseModel):
    message: str


@app.post("/echo")
def echo(body: EchoIn):
    return {"echo": body.message}


@app.get("/version")
def version():
    return {"version": APP_VERSION}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=8080, reload=True)
