from .llms import getAIModel
from .utils import State
from langchain.llms import BaseLLM
from langgraph.graph import END, START, StateGraph
from typing import Literal
from .guardrails import Guardrails
from .analyze_query import AnalyzeQuery
from .gather_context import GatherContext
from .find_context_relevance import FindContextRelevance
from .query import Query
import traceback

# -----------------------------------------------------------------------
def guardrails_condition(
        state: State,
    ) -> Literal['analyze_query', '__end__']:
        if state.get('next_action') == 'end':
            return END
        if state.get('next_action') == 'tox':
            return 'analyze_query'

# -----------------------------------------------------------------------
def validate_context_condition(
    state: State,
) -> Literal['query_without_context', '__end__']:
    return state.get('next_action')

# -----------------------------------------------------------------------
def createGraph(llm, use_training_data):

    # -----------------------------------------------------------------------
    # LLM
    # -----------------------------------------------------------------------
    # If agentic LLM is not provided, use a new one with model name = llm
    if isinstance(llm, str):
        llm = getAIModel(model_name=llm)

    # -----------------------------------------------------------------------
    # Langgraph
    # -----------------------------------------------------------------------
    gr = Guardrails(llm)
    aq = AnalyzeQuery(llm)
    gc = GatherContext()
    fc = FindContextRelevance(llm)
    qr = Query(llm)

    langgraph = StateGraph(State, input=State, output=State)

    if use_training_data:

        langgraph.add_node(aq.analyze_query)
        langgraph.add_node(gc.gather_context)
        #langgraph.add_node(find_context_relevance)
        langgraph.add_node(qr.query_with_context)
        langgraph.add_node(qr.query_without_context)

        use_guardrail = False
        if use_guardrail:
            langgraph.add_node(guardrails)
            langgraph.add_edge(START, 'guardrails')
            langgraph.add_conditional_edges(
                'guardrails',
                guardrails_condition,
            )
        else:
            langgraph.add_edge(START, 'analyze_query')

        langgraph.add_edge('analyze_query', 'gather_context')
        langgraph.add_edge('gather_context', 'query_with_context')
        langgraph.add_conditional_edges(
            'query_with_context',
            validate_context_condition,
        )
        langgraph.add_edge('query_without_context', END)

    else:

        langgraph.add_node(aq.analyze_query)
        langgraph.add_node(gc.gather_context)
        langgraph.add_node(qr.query_with_context)
        
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

        langgraph.add_edge('analyze_query', 'gather_context')
        langgraph.add_edge('gather_context', 'query_with_context')
        langgraph.add_edge('query_with_context', END)

    langgraph = langgraph.compile()

    return langgraph

# -----------------------------------------------------------------------
def query(query_text: str, llm: BaseLLM | str = 'azure-gpt-4o', use_training_data: bool = True) -> str:
    '''
    Provides response to user query
    
    :param query_text: User query
    :param llm: BaseLLM object or Name of the LLM
    :param use_training_data: If RAG should extract information from training data, 
                              when the RAG resources do not have the answer to user query
    :return: Response to user query, 
            Searched keyphrases from RAG DB, 
            Steps taken by the LLM to generate the response,
            Any errors during execution
    '''

    try:
        langgraph = createGraph(llm=llm, use_training_data=use_training_data)
        response = dict(langgraph.invoke(dict(query=query_text)))#, config={"callbacks": [Config.langfuse_handler]})
    except Exception as exp:
        response = {'error': f'Line number: {exp.__traceback__.tb_lineno}, Description: {exp}\n\n{traceback.format_exc()}'}
        print(response['error'])
    
    return {'response': response.get('response', ''), 
            'searched_keyphrases': response.get('keyphrases', []), 
            'steps_taken': response.get('steps', []), 
            'error': response.get('error', '')}