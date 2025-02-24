from .llms import getOpenAIModel
from .prompts import getPrompt, PromptPreRetrieval, PromptRAG
from .retrievers import CustomRetriever
from .output_parsers import CustomOutputParser, PreRetrievalOutputParserSchema

def createChains(llm, temperature):

    # -----------------------------------------------------------------------
    # LLM
    # -----------------------------------------------------------------------
    llm = getOpenAIModel(llm, temperature=temperature)

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
def query(query_text, llm='azure-gpt-4o', temperature=0):

    custom_chain_pr, custom_chain = createChains(llm=llm, temperature=temperature)

    keywords = custom_chain_pr.invoke(query_text)

    response = custom_chain.invoke(input=keywords | dict(query=query_text))#, config={"callbacks": [Config.langfuse_handler]})

    return response