
# -*- coding: utf-8 -*-
from typing import List, Union
from fastapi import FastAPI, Request
from app.agents import toxpipe as tp
import json
import datetime
import uuid
app = FastAPI()

AGENT_DICT = {}

@app.get("/agent/create/")
async def create(request: Request, model: str = "azure-gpt-4o", temp: float = 0, max_iterations: int = 10, n_threads: int = 1, summarize: bool = False):
    agent_name = uuid.uuid4()
    tpa = tp.ToxPipeAgent(name=agent_name, model=model, temp=temp, max_iterations=max_iterations, n_agents=n_threads, summarize=summarize, verbose=True, auth=False)
    AGENT_DICT[agent_name] = tpa
    return {"agentid": agent_name, "model": model, "temp": temp, "max_iterations": max_iterations, "n_threads":n_threads, "summarize":summarize, "date_created":datetime.datetime.now()}


@app.get("/agent/query/")
async def query(request: Request, agentid: uuid.UUID, q: str):    

    print("===AGENT_DICT===")
    print(AGENT_DICT)

    if agentid not in AGENT_DICT:
        return {"response": f"Error: agent {agentid} not found. Did you initialize the agent?"}
    tpa = AGENT_DICT[agentid]
    res = tpa.run(q)
    return {"response": res}