
# -*- coding: utf-8 -*-
from typing import List, Union
from fastapi import FastAPI, HTTPException, Depends
from app.agents import toxpipe as tp


app = FastAPI()

################


@app.get("/query/")
async def query(q: Union[str, None] = None, model: str = "azure-gpt-4o", temp: float = 0, max_iterations: int = 10, n_agents: int = 1, summarize: bool = False):
    tpa = tp.ToxPipeAgent(model=model, temp=temp, max_iterations=max_iterations, n_agents=n_agents, summarize=summarize, verbose=False, auth=False)
    res = tpa.run(q)
    return {"response": res}


#@app.get("/queryi/")
#async def query(token: Annotated[str, Depends(oauth2_scheme)], q: Union[str, None] = None, model: str = "azure-gpt-4o", temp: float = 0, max_iterations: int = 10, n_agents: int = 1, summarize: bool = False):
#    tpa = tp.ToxPipeAgent(model=model, temp=temp, max_iterations=max_iterations, n_agents=n_agents, summarize=summarize, verbose=False, auth=True)
#    res = tpa.run(q)
#    return {"response": res}
