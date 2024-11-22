
# -*- coding: utf-8 -*-
from typing import List, Union
from fastapi import FastAPI, HTTPException, Depends, Request, status
from app.agents import toxpipe as tp
import json
app = FastAPI()

################


# Authentication Check - from https://docs.posit.co/connect/user/plumber/
# Returns a list containing "user" and "groups" information 
# populated by incoming request data.
def getUserMetadata(req):
    raw_user_data = None
    if "rstudio-connect-credentials" in req:
        json_str = req["rstudio-connect-credentials"]
        user = json.loads(json_str)
        if "user" in user:
            raw_user_data = user["user"]
    print(raw_user_data)
    return(raw_user_data)

################


@app.get("/query/")
async def query(q: Union[str, None] = None, model: str = "azure-gpt-4o", temp: float = 0, max_iterations: int = 10, n_agents: int = 1, summarize: bool = False):
    tpa = tp.ToxPipeAgent(model=model, temp=temp, max_iterations=max_iterations, n_agents=n_agents, summarize=summarize, verbose=False, auth=False)
    res = tpa.run(q)
    return {"response": res}


#@app.get("/queryi/")
#async def query(request: Request, q: Union[str, None] = None, model: str = "azure-gpt-4o", temp: float = 0, max_iterations: int = 10, n_agents: int = 1, summarize: bool = False):
#    if getUserMetadata(req=request.headers) is not None:
#        tpa = tp.ToxPipeAgent(model=model, temp=temp, max_iterations=max_iterations, n_agents=n_agents, summarize=summarize, verbose=False, auth=True)
#        res = tpa.run(q)
#        return {"response": res}
#    else:
#        raise HTTPException(
#                status_code=status.HTTP_401_UNAUTHORIZED,
#                detail="Unauthorized: this endpoint is only available to internal NIEHS users. Please log in with your credentials and try again."