from .llms import getOpenAIModel
from .prompts import getPrompt, PromptPreRetrieval, PromptRAG
from .retrievers import CustomRetriever
from .output_parsers import CustomOutputParser, PreRetrievalOutputParserSchema
from langchain.llms import BaseLLM

def createChains(llm):

    # -----------------------------------------------------------------------
    # LLM
    # -----------------------------------------------------------------------
    # inherit from agentic LLM

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
    output_parser_pr = CustomOutputParser(PreRetrievalOutputParserSchema)
    output_parser = CustomOutputParser()

    # -----------------------------------------------------------------------
    # Chain
    # -----------------------------------------------------------------------
    custom_chain_pr = (
        prompt_pr 
        | llm 
        | output_parser_pr.parseKWOutput
    )

    custom_chain = (
        {'resources': retriever.getResources, 'query': lambda x: x['query']}
        | prompt
        | llm
        | output_parser.parseResOutput
    )

    return custom_chain_pr, custom_chain

# -----------------------------------------------------------------------
def query(query_text: str, llm: BaseLLM) -> str:
    '''
    Provides response to user query
    
    :param query_text: User query
    :param llm: Name of the LLM
    :param temperature: Temperature
    :return: Response to user query
    '''

    custom_chain_pr, custom_chain = createChains(llm=llm)

    keywords = custom_chain_pr.invoke(query_text)

    response = custom_chain.invoke(input=keywords | dict(query=query_text))#, config={"callbacks": [Config.langfuse_handler]})

    return response