from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from mcp_instance import mcp
from request_context import set_request
import tools  


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def set_request_context(request: Request, call_next):
    set_request(request)
    return await call_next(request)


@app.get("/hello-world")
async def health():
    return "Hello World"


app.mount("/", mcp.streamable_http_app())
