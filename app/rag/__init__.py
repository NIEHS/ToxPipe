from .llms import getOpenAIModel
from .utils import State
from langchain.llms import BaseLLM
from langgraph.graph import END, START, StateGraph
from typing import Literal
from .guardrails import Guardrails
from .analyze_query import AnalyzeQuery
from .gather_context import GatherContext
from .query import Query
import traceback

def guardrails_condition(
        state: State,
    ) -> Literal['analyze_query', '__end__']:
        if state.get('next_action') == 'end':
            return END
        if state.get('next_action') == 'tox':
            return 'analyze_query'

def validate_context_condition(
    state: State,
) -> Literal['query_without_context', '__end__']:
    if state.get('next_action') == 'end':
        return END
    if state.get('next_action') == 'query_without_context':
        return 'query_without_context'

def createGraph(llm):

    # -----------------------------------------------------------------------
    # LLM
    # -----------------------------------------------------------------------
    # If agentic LLM is not provided, use a new one with model name = llm
    if isinstance(llm, str):
        llm = getOpenAIModel(llm)

    gr = Guardrails(llm)
    aq = AnalyzeQuery(llm)
    gc = GatherContext()
    qr = Query(llm)

    # -----------------------------------------------------------------------
    # Langgraph
    # -----------------------------------------------------------------------
    langgraph = StateGraph(State, input=State, output=State)
    use_guardrail = False
    if use_guardrail:
        langgraph.add_node(gr.guardrails)
        langgraph.add_edge(START, 'guardrails')
        langgraph.add_conditional_edges(
            'guardrails',
            guardrails_condition,
        )
    else:
        langgraph.add_edge(START, 'analyze_query')
    langgraph.add_node(aq.analyze_query)
    langgraph.add_node(gc.gather_context)
    langgraph.add_node(qr.query_with_context)
    langgraph.add_node(qr.query_without_context)
    langgraph.add_edge('analyze_query', 'gather_context')
    langgraph.add_edge('gather_context', 'query_with_context')
    langgraph.add_conditional_edges(
        'query_with_context',
        validate_context_condition,
    )
    langgraph.add_edge('query_without_context', END)

    langgraph = langgraph.compile()

    return langgraph

# -----------------------------------------------------------------------
def query(query_text: str, llm: BaseLLM | str = 'azure-gpt-4o') -> str:
    '''
    Provides response to user query
    
    :param query_text: User query
    :param llm: BaseLLM object or Name of the LLM
    :return: Response to user query, 
            Searched keyphrases from RAG DB, 
            Steps taken by the LLM to generate the response,
            Any errors during execution
    '''
    response, error = {'response': ''}, ''
    try:
        langgraph = createGraph(llm=llm)
        response = dict(langgraph.invoke(dict(query=query_text)))#, config={"callbacks": [Config.langfuse_handler]})
    except Exception as exp:
        error = f'Line number: {exp.__traceback__.tb_lineno}, Description: {exp}\n\n{traceback.format_exc()}'
        print(error)
    
    return {'response': response['response'], 'searched_keyphrases': response['keyphrases'], 'steps_taken': response['steps'], 'error': error}