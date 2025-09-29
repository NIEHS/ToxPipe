# Force app to use system cert store instead of certifi
import truststore

import atexit

# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request, Response

from app.agents import toxpipe as tp
from app.agents import tools as tl
from app.rag import query

from langchain.tools.render import render_text_description
import json
import datetime
import uuid
from langgraph.checkpoint.postgres import PostgresSaver, ShallowPostgresSaver 
from psycopg_pool import ConnectionPool
import os
import ssl
import tempfile
from dotenv import dotenv_values
from pathlib import Path
DIR_HOME = Path(__file__).parent
env_config = dotenv_values(DIR_HOME / ".config" / ".env")
import requests
import traceback
import httpx
import certifi

# For NIEHS cert issue
#ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
#ctx.load_verify_locations(f"{DIR_HOME}/{env_config['SSL_CERT_DIR']}/NIH-FULL.pem")
#ctx.verify_mode = ssl.CERT_REQUIRED
#ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
#ctx = ssl.create_default_context()
#ctx.load_cert_chain(certfile=f"{DIR_HOME}/{env_config['SSL_CERT_DIR']}/NIH-FULL.pem") 
ctx = ssl.create_default_context(cafile=f"{DIR_HOME}/{env_config['SSL_CERT_DIR']}/NIH-FULL.pem")  # Either cafile or capath.
client = httpx.Client(verify=ctx)
#truststore.inject_into_ssl()
 
# Persistent memory
# Establish Postgres Connection for ToxPipe
postgres_host = env_config["TOXPIPE_POSTGRES_HOST"]
postgres_port = env_config["TOXPIPE_POSTGRES_PORT"]
postgres_name = env_config["TOXPIPE_POSTGRES_DATABASE"]
postgres_user = env_config["TOXPIPE_POSTGRES_USER"]
postgres_pass = env_config["TOXPIPE_POSTGRES_PASSWORD"]
DB_URI = f"postgresql://{postgres_user}:{postgres_pass}@{postgres_host}:{postgres_port}/{postgres_name}"
connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}
pool = ConnectionPool(conninfo=DB_URI, max_size=20, kwargs=connection_kwargs,)
checkpointer = ShallowPostgresSaver(pool)
#checkpointer = PostgresSaver(pool)
checkpointer.setup()

def exit_handler():
    print("Shutting down...")
    pool.close()
    print("Connection pool closed.")

atexit.register(exit_handler)

tags_metadata = [
    {
        "name": "agent",
        "description": "Endpoints for creating and query agents.",
    },
    {
        "name": "models",
        "description": "Endpoints for viewing supported models and tools available to them.",
    },
    {
        "name": "rag",
        "description": "Endpoints for searching through text embeddings created from documents processed with OCR.",
    },
    {
        "name": "util",
        "description": "Endpoints for API utility functions.",
    },
]

app = FastAPI(
    title="ToxPipe Agentic API",
    description="An API for creating custom LLM agents for performing chat completions with specialized tool access. Part of the ToxPipe ecosystem.",
    version="0.0.1",
    openapi_tags=tags_metadata,
)

# session cache for storing created agents so the API doesn't have to keep recreating them
AGENT_DICT = {}

# Supported models
ANTHROPIC_MODELS = ['claude-3-7-sonnet', 'claude-3-5-sonnet', 'claude-3-sonnet', 'claude-3-haiku', 'claude-3-opus'] # haiku and opus work better
OLLAMA_MODELS = ['llama3-3-70b', 'llama3-1-70b', 'llama3-1-8b', 'openbiollm-llama3-70b'] # These have trouble with tools
OPENAI_MODELS = ['azure-gpt-4o', 'azure-gpt-3.5-turbo', 'azure-gpt-4o-mini', 'azure-gpt-3.5-turbo-16k', 'azure-gpt-4-turbo-20240409', 'azure-gpt-4', 'azure-o3', 'azure-o3-mini', 'azure-o1', 'azure-o1-mini'] # These all work pretty well
MISTRALAI_MODELS = ['mistral-large-2', 'mistral-large', 'mistral-7b-instruct', 'mixtral-8x7b-instruct'] # mistral-large-2 and mixtral-8x7b-instruct has issues accessing tools
GOOGLE_MODELS = ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-1.5-pro'] # TODO - VertexAIException BadRequestError - "Unable to submit request because one or more function parameters didn\'t specify the schema type field. Learn more: https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling
AMAZON_MODELS = ['amazon-titan-text-premier']
COHERE_MODELS = ['cohere-command-r-plus']

# Load environment variables from .config/.env
AUTH_MODE = env_config["TOXPIPE_AUTH_MODE"] # Should usually be false unless running a secure, internal-to-NIEHS version of this API
VERBOSE = env_config["TOXPIPE_VERBOSE"] # Should be false on production
CACHE = env_config["TOXPIPE_CACHE"] 

# Convert environment variables to boolean if they are strings
if AUTH_MODE == "True":
    AUTH_MODE = True
elif AUTH_MODE == "False":    
    AUTH_MODE = False
else:
    raise ValueError("TOXPIPE_AUTH_MODE must be set to either 'True' or 'False' in the .env file.")

if VERBOSE == "True":
    VERBOSE = True
elif VERBOSE == "False":    
    VERBOSE = False
else:
    raise ValueError("TOXPIPE_VERBOSE must be set to either 'True' or 'False' in the .env file.")

if CACHE == "True":
    CACHE = True
elif CACHE == "False":    
    CACHE = False
else:
    raise ValueError("TOXPIPE_CACHE must be set to either 'True' or 'False' in the .env file.")

MODEL_CACHE = {}

# Endpoint for basic API instructions
@app.get("/help/")
async def help(request: Request, response: Response):
    return {"response": f"Use the /agent/create/ endpoint to define an agent with the specified parameters. If the agent was successfully created, this endpoint will return a UUID for the agent. Use the /agent/query/ endpoint to query the agent with the specified UUID and query string. Increasing agent temperature may increase answer variance, but may also increase the likelihood of nonsensical answers. Increasing max iterations may help for complex queries that need many steps to process. Increasing max retries may help if queries to the agent repeatedly fail. Setting n_threads > 1 spawns n_threads copies of the agent to process the query in parallel, which may generate a more comprehensive answer; when n_threads = 1, only a single instance of the agent is run. When summarize is set to True, the agent will attempt to summarize the output of the query: this is automaticalyl set to true when n_threads > 1."}

# Endpoint for creating an agent. Note that this will not actually create the agent object in memory, it just creates a JSON file with the agent parameters so that the API is "aware" that such an agent is defined and may be created later.
@app.get("/agent/create/", tags=["agent"])
async def create_agent(request: Request, response: Response, model: str = "azure-gpt-5-nano", temp: float = 0, max_iterations: int = 20, max_retries: int = 10, max_tokens: int=4096, max_memory_tokens: int=4096, step_timeout: float = 0, n_threads: int = 1, summarize: bool = False, seed: int = 1):
    # Input validation
    #if model not in ANTHROPIC_MODELS and model not in OLLAMA_MODELS and model not in OPENAI_MODELS and model not in MISTRALAI_MODELS and model not in GOOGLE_MODELS and model not in AMAZON_MODELS and model not in COHERE_MODELS:
    #    response.status_code = 400
    #    return {"response": f"Error: model '{model}' is not supported by ToxPipe. Please check your spelling and try again. Use the /models endpoint to view a list of supported models."}
    if temp < 0 or temp > 1:
        response.status_code = 400
        return {"response": f"Error: temperature must be between 0 and 1 (inclusive)."}
    if n_threads > 5 or n_threads < 1:
        response.status_code = 400
        return {"response": f"Error: 'n_threads' must be between 1 and 5 (inclusive)."}
    agentid = uuid.uuid4() # Generate UUID for the agent
    agent = {"agentid": str(agentid), "model": model, "temp": temp, "max_iterations": max_iterations, "max_retries":max_retries, "max_tokens":max_tokens, "max_memory_tokens":max_memory_tokens, "step_timeout":step_timeout, "n_threads":n_threads, "summarize":summarize, "seed":seed, "date_created":str(datetime.datetime.now())}
    # Create a JSON file with the agent parameters
    os.makedirs("./created_agents", exist_ok=True)
    with open(f"./created_agents/{agentid}.json", 'w') as fp:
        json.dump(agent, fp)
    return agent

# Endpoint for querying an agent. This will create the agent from the JSON file (or load it from the cache if it has been previously loaded) and run the query. If the agent is not found, the API will return an error message. 
@app.get("/agent/query/", tags=["agent"])
async def query_agent(request: Request, response: Response, agentid: uuid.UUID, q: str):    
    tpa = None

    # Check if the agent is in the cache. If not, then generate the agent from the JSON file and save to cache.
    if agentid not in MODEL_CACHE:
        try:
            with open(f"./created_agents/{agentid}.json", 'r') as fp:
                agent = json.load(fp)
                tpa = tp.ToxPipeAgent(name=agent["agentid"], model=agent["model"], client=client, temp=agent["temp"], max_iterations=agent["max_iterations"], max_retries=agent["max_retries"],  max_tokens=agent["max_tokens"], max_memory_tokens=agent["max_memory_tokens"], step_timeout=agent["step_timeout"], n_agents=agent["n_threads"], summarize=agent["summarize"], verbose=VERBOSE, auth=AUTH_MODE, checkpointer=checkpointer, cache=CACHE, seed=agent["seed"])
                MODEL_CACHE[agentid] = tpa

        except Exception as e:
            print("Error loading agent from file.")
            print(f'error: Line number: {e.__traceback__.tb_lineno}, Description: {e}\n\n{traceback.format_exc()}')
            tpa = None
    # Otherwise, just load the agent from the cache.
    else:
        print("Fetching agent from cache")
        tpa = MODEL_CACHE[agentid]

    if tpa is None:
        response.status_code = 400
        return {"response": f"Error: agent {agentid} not found or unable to be loaded. Did you initialize the agent?"}
    
    res = None

    try:
        res = tpa.run(q)
    except Exception as e:
        print("Error running agent.")
        exp = {'error': f'Line number: {e.__traceback__.tb_lineno}, Description: {e}\n\n{traceback.format_exc()}'}
        print(exp)
        response.status_code = 400
        return {"response": f"Error: agent {agentid} failed to run with message: {exp}."}
    
    return {"response": res}

# Endpoint for querying an agent specifically using RAG and no additional tools. This will create the agent from the JSON file (or load it from the cache if it has been previously loaded) and run the query. If the agent is not found, the API will return an error message.
@app.get("/agent/rag/", tags=["agent"])
async def query_rag(request: Request, response: Response, agentid: uuid.UUID, q: str, use_training_data: bool = True):    
    tpa = None

    if agentid not in MODEL_CACHE:
        try:
            with open(f"./created_agents/{agentid}.json", 'r') as fp:
                agent = json.load(fp)
                tpa = tp.ToxPipeAgent(name=agent["agentid"], model=agent["model"], client=client, temp=agent["temp"], max_iterations=agent["max_iterations"], max_retries=agent["max_retries"],  max_tokens=agent["max_tokens"], max_memory_tokens=agent["max_memory_tokens"], step_timeout=agent["step_timeout"], n_agents=agent["n_threads"], summarize=agent["summarize"], verbose=VERBOSE, auth=AUTH_MODE, checkpointer=checkpointer, cache=CACHE, seed=agent["seed"])
                MODEL_CACHE[agentid] = tpa

        except Exception as e:
            print("Error loading agent from file.")
            print(f'error: Line number: {e.__traceback__.tb_lineno}, Description: {e}\n\n{traceback.format_exc()}')
            print(e)
            tpa = None
    else:
        print("Fetching agent from cache")
        tpa = MODEL_CACHE[agentid]

    if tpa is None:
        response.status_code = 400
        return {"response": f"Error: agent {agentid} not found or unable to be loaded. Did you initialize the agent?"}
    
    res = None

    try:
        res = tpa.run_rag(q, use_training_data)
    except Exception as e:
        print("Error running agent.")
        print(e)
        response.status_code = 400
        return {"response": f"Error: agent {agentid} failed to run with message: {e}."}
    
    return {"response": res}

# Endpoint for querying an agent specifically using a literature search and no additional tools. This will create the agent from the JSON file (or load it from the cache if it has been previously loaded) and run the query. If the agent is not found, the API will return an error message.
@app.get("/agent/literature/", tags=["agent"])
async def query_literature(request: Request, response: Response, agentid: uuid.UUID, q: str):    
    tpa = None

    if agentid not in MODEL_CACHE:
        try:
            with open(f"./created_agents/{agentid}.json", 'r') as fp:
                agent = json.load(fp)
                tpa = tp.ToxPipeAgent(name=agent["agentid"], model=agent["model"], client=client, temp=agent["temp"], max_iterations=agent["max_iterations"], max_retries=agent["max_retries"],  max_tokens=agent["max_tokens"], max_memory_tokens=agent["max_memory_tokens"], step_timeout=agent["step_timeout"], n_agents=agent["n_threads"], summarize=agent["summarize"], verbose=VERBOSE, auth=AUTH_MODE, checkpointer=checkpointer, cache=CACHE, seed=agent["seed"])
                MODEL_CACHE[agentid] = tpa

        except Exception as e:
            print("Error loading agent from file.")
            print(f'error: Line number: {e.__traceback__.tb_lineno}, Description: {e}\n\n{traceback.format_exc()}')
            tpa = None
    else:
        print("Fetching agent from cache")
        tpa = MODEL_CACHE[agentid]

    if tpa is None:
        response.status_code = 400
        return {"response": f"Error: agent {agentid} not found or unable to be loaded. Did you initialize the agent?"}
    
    res = None

    try:
        res = tpa.run_lit(q)
    except Exception as e:
        print("Error running agent.")
        print(e)
        response.status_code = 400
        return {"response": f"Error: agent {agentid} failed to run with message: {e}."}
    
    return {"response": res}



# Endpoint for directly querying the RAG search
@app.get("/rag/", tags=["rag"])
async def query_rag(request: Request, response: Response, model: str, q: str, use_training_data: bool = True):    
    tpa = None
    res = None

    try:
        res = query(q, llm=model, use_training_data=use_training_data)
    except Exception as e:
        print("Error performing search.")
        print(e)
        response.status_code = 400
        return {"response": f"Error: query failed to run with message: {e}."}
    
    return {"response": res}

# Endpoint for viewing a list of supported models.
@app.get("/models", tags=["models"])
async def view_supported_models(request: Request, response: Response):
    return {"ANTHROPIC_MODELS": ANTHROPIC_MODELS, "OLLAMA_MODELS": OLLAMA_MODELS, "OPENAI_MODELS": OPENAI_MODELS, "MISTRALAI_MODELS": MISTRALAI_MODELS, "GOOGLE_MODELS": GOOGLE_MODELS, "AMAZON_MODELS": AMAZON_MODELS, "COHERE_MODELS": COHERE_MODELS}

# Endpoint for viewing a list of supported tools for an agent.
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


# Check if this API can connect to the llm provider.
@app.get("/heartbeat", tags=["util"])
async def check_api_connections(request: Request, response: Response):

    llm_res = None
    cbt_res = None

    try:
        llm_res = requests.get(
            f"{env_config['OPENAI_BASE_URL']}/",
            headers={'Authorization': f"Bearer {env_config['OPENAI_API_KEY']}"}
        ).status_code
        if llm_res == 200:
            llm_res = "Connected!"
        if llm_res >= 400 :
            llm_res = "Connected but ran into an error!"
    except requests.exceptions.SSLError as e:
        llm_res = "Could not connect: SSLError!"
    except:
        llm_res = "Could not connect to API!"

    
    
    try:
        cbt_res = requests.get(
            f"{env_config['CBT_API_ENDPOINT']}/",
            headers={'Authorization': f"Key {env_config['CONNECT_API_KEY']}"}
        ).status_code
        if cbt_res == 200:
            cbt_res = "Connected!"
        if cbt_res >= 400 :
            cbt_res = "Connected but ran into an error!"
    except requests.exceptions.SSLError as e:
        cbt_res = "Could not connect: SSLError!"
    except:
        cbt_res = "Could not connect to API!"

    return {
        "LLM Provider API": llm_res,
        "ChemBioTox API": cbt_res
    }

