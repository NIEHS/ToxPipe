from .llms import getOpenAIModel
from .prompts import getPrompt, PromptPreRetrieval, PromptRAG
from .retrievers import CustomRetriever
from .output_parsers import CustomPreRetrievalOutputParser, CustomOutputParser
from langchain.llms import BaseLLM
from langchain_openai import AzureChatOpenAI
import traceback

def createChains(llm):

    # -----------------------------------------------------------------------
    # LLM
    # -----------------------------------------------------------------------
    # If agentic LLM is not provided, use a new one with model name = llm
    if isinstance(llm, str):
        llm = getOpenAIModel(llm)

    # -----------------------------------------------------------------------
    # Prompt
    # -----------------------------------------------------------------------
    prompt_pr = getPrompt(PromptPreRetrieval)
    prompt = getPrompt(PromptRAG)

    # -----------------------------------------------------------------------
    # Retriever
    # -----------------------------------------------------------------------
    retriever = CustomRetriever()

    # -----------------------------------------------------------------------
    # Output parser
    # -----------------------------------------------------------------------
    output_parser_pr = CustomPreRetrievalOutputParser()
    output_parser = CustomOutputParser()

    # -----------------------------------------------------------------------
    # Chain
    # -----------------------------------------------------------------------
    custom_chain_pr = (
        prompt_pr 
        | llm#.with_structured_output(PreRetrievalOutputParserSchema)
        | output_parser_pr.parseOutput
    )

    custom_chain = (
        {'resources': retriever.getResources, 'query': lambda x: x['query']}
        | prompt
        | llm#.with_structured_output(OutputParserSchema)
        | output_parser.parseOutput
    )

    return custom_chain_pr, custom_chain

# -----------------------------------------------------------------------
def query(query_text: str, llm: BaseLLM | str = 'azure-gpt-4o') -> str:
    '''
    Provides response to user query
    
    :param query_text: User query
    :param llm: BaseLLM object or Name of the LLM
    :return: Response to user query
    '''
    response, keywords, error = {'Response': ''}, {'Keywords': []}, ''
    try:
        custom_chain_pr, custom_chain = createChains(llm=llm)
        keywords = dict(custom_chain_pr.invoke(query_text))
        response = dict(custom_chain.invoke(input=keywords | dict(query=query_text)))#, config={"callbacks": [Config.langfuse_handler]})

    except Exception as exp:
        error = f'Line number: {exp.__traceback__.tb_lineno}, Description: {exp}\n\n{traceback.format_exc()}'
        print(error)
        breakpoint()
    
    return {'response': response['Response'], 'searched_keyphrases': keywords['Keywords'], 'error': error}