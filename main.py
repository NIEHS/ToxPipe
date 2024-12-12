
# -*- coding: utf-8 -*-
from typing import List, Union
from fastapi import FastAPI, Request, Response
from app.agents import toxpipe as tp
from app.agents import tools as tl
from langchain.tools.render import render_text_description
import json
import datetime
import uuid

tags_metadata = [
    {
        "name": "agent",
        "description": "Endpoints for creating and query agents.",
    },
    {
        "name": "models",
        "description": "Endpoints for viewing supported models and tools available to them.",
    },
]

app = FastAPI(
    title="ToxPipe Agentic API",
    description="An API for creating custom LLM agents for performing chat completions with specialized tool access. Part of the ToxPipe ecosystem.",
    version="0.0.1",
    openapi_tags=tags_metadata,
)

AGENT_DICT = {}
ANTHROPIC_MODELS = ['claude-3-5-sonnet', 'claude-3-sonnet', 'claude-3-haiku', 'claude-3-opus'] # haiku and opus work better
OLLAMA_MODELS = ['llama3-1-70b', 'llama3-1-8b', 'openbiollm-llama3-70b', 'llama2-13b'] # These have trouble with tools
OPENAI_MODELS = ['azure-gpt-4o', 'azure-gpt-3.5-turbo', 'azure-gpt-4o-mini', 'azure-gpt-3.5-turbo-16k', 'azure-gpt-4-turbo-20240409', 'azure-gpt-4'] # These all work pretty well
MISTRALAI_MODELS = ['mistral-large-2', 'mistral-large', 'mistral-7b-instruct', 'mixtral-8x7b-instruct'] # mistral-large-2 and mixtral-8x7b-instruct has issues accessing tools
GOOGLE_MODELS = ['gemini-1.5-pro'] # TODO - VertexAIException BadRequestError - "Unable to submit request because one or more function parameters didn\'t specify the schema type field. Learn more: https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling
AMAZON_MODELS = ['amazon-titan-text-premier']
COHERE_MODELS = ['cohere-command-r-plus']

# Must be False for public API, True for Private API. When in doubt, set to False.
AUTH_MODE = False

@app.get("/agent/create/", tags=["agent"])
async def create_agent(request: Request, response: Response, model: str = "azure-gpt-4o", temp: float = 0, max_iterations: int = 10, step_timeout: float = 0, n_threads: int = 1, summarize: bool = False):

    # Input validation
    if model not in ANTHROPIC_MODELS and model not in OLLAMA_MODELS and model not in OPENAI_MODELS and model not in MISTRALAI_MODELS and model not in GOOGLE_MODELS and model not in AMAZON_MODELS and model not in COHERE_MODELS:
        response.status_code = 400
        return {"response": f"Error: model '{model}' is not supported by ToxPipe. Please check your spelling and try again. Use the /models endpoint to view a list of supported models."}
    if temp < 0 or temp > 1:
        response.status_code = 400
        return {"response": f"Error: temperature must be between 0 and 1 (inclusive)."}
    if n_threads > 5:
        response.status_code = 400
        return {"response": f"Error: 'n_threads' must be 5 or less."}

    agent_name = uuid.uuid4()
    tpa = tp.ToxPipeAgent(name=agent_name, model=model, temp=temp, max_iterations=max_iterations, step_timeout=step_timeout, n_agents=n_threads, summarize=summarize, verbose=True, auth=AUTH_MODE)
    AGENT_DICT[agent_name] = tpa
    return {"agentid": agent_name, "model": model, "temp": temp, "max_iterations": max_iterations, "step_timeout":step_timeout, "n_threads":n_threads, "summarize":summarize, "date_created":datetime.datetime.now()}


@app.get("/agent/query/", tags=["agent"])
async def query_agent(request: Request, response: Response, agentid: uuid.UUID, q: str):    
    if agentid not in AGENT_DICT:
        response.status_code = 400
        return {"response": f"Error: agent {agentid} not found. Did you initialize the agent?"}
    tpa = AGENT_DICT[agentid]
    res = tpa.run(q)
    return {"response": res}

@app.get("/models", tags=["models"])
async def view_supported_models(request: Request, response: Response):
    return {"ANTHROPIC_MODELS": ANTHROPIC_MODELS, "OLLAMA_MODELS": OLLAMA_MODELS, "OPENAI_MODELS": OPENAI_MODELS, "MISTRALAI_MODELS": MISTRALAI_MODELS, "GOOGLE_MODELS": GOOGLE_MODELS, "AMAZON_MODELS": AMAZON_MODELS, "COHERE_MODELS": COHERE_MODELS}

@app.get("/models/tools", tags=["models"])
async def view_available_tools(request: Request, response: Response):
    tools = render_text_description(tl.make_tools(llm=None, auth=AUTH_MODE))

    tools = str(tools).split("\n")

    tools_to_return = []
    for tool in tools:
        tmpsplit = tool.split(" - ")
        if len(tmpsplit) == 2:
            tools_to_return.append({"tool_name": tmpsplit[0], "tool_description": tmpsplit[1]})

    
    return tools_to_return