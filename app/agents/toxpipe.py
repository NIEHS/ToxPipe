# LangChain/Graph agent creation
from .toxpipe_agent_executor import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph.message import add_messages
# Model interface
from langchain_openai import AzureChatOpenAI
# Memory & Cache
from langchain_core.messages import BaseMessage
from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
# File management & Tools
from tempfile import TemporaryDirectory
from langchain_community.agent_toolkits import FileManagementToolkit
# Create temporary working directory
working_directory = TemporaryDirectory()
toolkit = FileManagementToolkit(
    root_dir=str(working_directory.name)
)  # If you don't provide a root_dir, operations will default to the current working directory
tools = FileManagementToolkit(
    root_dir=str(working_directory.name),
    selected_tools=["read_file", "write_file", "list_directory"],
).get_tools()
read_tool, write_tool, list_tool = tools

from .tools import make_tools
# Multiprocessing
import concurrent.futures
from .multi import *
# Load environment variables
from dotenv import load_dotenv
load_dotenv('../.config/.env')
# Prompts
from .prompts_chem import PROMPT
# Other
from typing import Sequence
from typing_extensions import Annotated, TypedDict
import os

from ..rag import query

# Handle models that have issues reading tools via LangChain's tool API. We will have to add these manually as a prompt.
BAD_TOOL_MODELS = ['mistral-large-2', 'mistral-large', 'mistral-7b-instruct', 'mixtral-8x7b-instruct', 'llama3-1-70b', 'claude-3-sonnet', 'amazon-titan-text-premier', 'cohere-command-r-plus']

def _make_llm(model, api_version, temp, max_retries, seed):
    llm = AzureChatOpenAI(
        model_name=model,
        temperature=temp,
        max_retries=max_retries,
        seed=seed
    )
    return llm

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

class ToxPipeAgent:
    """
    ToxPipeAgent is based on the ChemCrow agent that provides a simple interface for querying a LLM using the agent on a given prompt.
    """
    def __init__(
        self,
        name,
        model,
        api_version=os.environ.get("OPENAI_API_VERSION"),
        temp=0.0, # higher temperature creates more answer variance, but this is potentially better if we are doing a multi-agent approach
        max_iterations=10, # maximum number of agent recursions in chain
        max_retries=100, # maximum number of retries upon LLM failure - set this to finite to avoid token limit errors from OpenAI
        step_timeout=0, # maximum time in seconds to take per recursion
        n_agents=1, # number of parallel agents to run - set to 1 for no parallelism. Higher values better for more complicated queries to help reduce variance
        summarize=False, # if True, will summarize output. Ignored and always treated as True if n_agents > 1.
        verbose=False,
        auth=False,
        checkpointer=None,
        cache=False, # If true, will cache repeat requests to avoid making duplicate API calls
        seed=1
    ):
        self.llm = _make_llm(model, api_version, temp, max_retries, seed)
        if cache == True:
            set_llm_cache(SQLiteCache(database_path=".langchain.db")) # set cache to avoid making the same API calls over and over again
        self.tools = make_tools(self.llm, verbose=verbose, auth=auth)
        self.n_agents = n_agents
        self.summarize = summarize
        self.max_iterations = max_iterations
        self.max_retries = max_retries
        self.thread_id = name
        self.checkpointer = checkpointer
        self.seed = seed
        manual_tool_support = []

        # If we use a model that doesn't fully support tools, then we need to manually add the tools as part of the prompt
        if model in BAD_TOOL_MODELS:
            manual_tool_support = self.tools

        # Initialize agent to add tools to model
        agent_executor = create_react_agent(self.llm, self.tools, state_modifier=PROMPT, checkpointer=checkpointer, manual_tool_support=manual_tool_support, debug=verbose) # state_modifier=PROMPT adds the prompt instructions to the agent
        if step_timeout > 0:
            agent_executor.step_timeout = step_timeout

        self.agent_with_chat_history = agent_executor
        self.config = {"configurable": {"thread_id": self.thread_id}, "recursion_limit": self.max_iterations}

    @classmethod
    def is_lc_serializable(cls) -> bool:
        return True


    def run(self, input):
        n_agents = self.n_agents
        proc = []
        res = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_agents) as executor:
            for i in range(0, n_agents):
                proc.append(executor.submit(run_parallel, self, input, i))
        i = 0    
        for future in concurrent.futures.as_completed(proc):
            fr = f"{future.result()}"
            res.append(fr)
            i += 1
        res = "\n\n".join(res)

        if self.summarize == False and n_agents == 1:
            return res

        summary_prompt_template = """
        Previously, {n_agents} separate LLM agents were run to answer the following input from an end user:

        {input}

        The following are the raw results from each agent:

        {res}

        Using these responses, reformat the responses into a single response to be returned to the end user.
        IMPORTANT: you MUST follow the following steps when formulating your final response:
            1. This summary should contain the most relevant information from the raw results that answers the original input. Try to only include information that is relevant to the original input and avoid including any irrelevant information.
            2. If there are any discrepancies between the raw results, try to resolve them in the summary.
            3. If there are any contradictions between the raw results, try to explain why these contradictions exist and what the implications are for the end user.
            4. If there are any uncertainties in the raw results, try to explain why these uncertainties exist and what the implications are for the end user.
            5. If there are any limitations in the raw results, try to explain what these limitations are and how they affect the end user.
            6. If there are any other important details in the raw results that are relevant to the end user, try to include these in the summary as well.
            7. You MUST include a "confidence rating" for each piece of information in the summary that indicates how confident you are in that piece of information. This confidence rating should be the number of agents that returned that piece of information divided by the total number of agents, {n_agents} and formatted as a percentage.
            8. If there is information that is only present in a minority of the agent responses, explain that this information has a low confidence rating.
            9. Rank the information in descending order of confidence, with the most confident items at the top of the list.
            10. If they are available, you must include the source for ALL information returned in the summary. This includes the source for the raw results from each agent as well as the source for any additional information that you include in the summary.
            11. Maintain as much of the original information and formatting as possible from the raw results when creating the final response. This includes any lists, tables, sources, or other formatting that was present in the raw results.
            12. If asked to provide a list of chemicals, like metabolites, you must include the full list in the summary without summarizing or grouping the list.
            13. When providing the sources for information, you must include each source's author(s), title, date of publication, journal of publication, and DOI, URL, or PMID if available in the final summary.
            14. You MUST provide each agent's raw response WITHOUT SUMMARIZING above the final summary, noting which agent produced which result.
        """
        summary_prompt = ChatPromptTemplate.from_template(summary_prompt_template)
        summary_chain = summary_prompt | self.llm
        summary = summary_chain.invoke({"n_agents": n_agents, "input": input, "res": res})

        return summary.content
    
    def run_rag(self, input):
        try:
            rag_res = query(input, llm=self.llm)
            if(len(rag_res) < 1):
                return f"RAG did not find any results for query: {input}."
            return rag_res
        except Exception as e:
            print("Error running RAG.")
            print(e)
            return f"Error: RAG failed to run with message: {e}."
    
