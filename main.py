
# -*- coding: utf-8 -*-
import os
from datetime import date
from typing import List, Union

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.agents import toxpipe as tp

app = FastAPI(
    title="ToxPipe API",
    description="The ToxPipe API assists in finding relevant toxicological data for performing agentic queries.",
    docs_url="/docs"
)

@app.get("/", include_in_schema=False)
def docs_redirect():
    RedirectResponse(url='/docs')

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.get("/query/")
def query(q: Union[str, None] = None, model: str = "azure-gpt-4o", temp: float = 0, max_iterations: int = 10, n_agents: int = 1, summarize: bool = False):
    tpa = tp.ToxPipeAgent(model=model, temp=temp, max_iterations=max_iterations, n_agents=n_agents, summarize=summarize, verbose=False)
    res = tpa.run(q)
    return {"response": res}

