from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from .utils import Config

# ---------------------------------------------------------------------------
def getAIModel(model_name: str, temperature: int = 0, is_embedding=False) -> ChatOpenAI | OpenAIEmbeddings:
    """
    Initializes either an OpenAI Chat LLM object based on the LLM name and temperature
    or an OpenAI embedding model

    :param model_name: Name of the LLM
    :param temperature: Temperature
    :param is_embedding: For embedding model
    :return: OpenAI Chat LLM
    """

    if not is_embedding:
    
        return ChatOpenAI(
            model=model_name,
            base_url=Config.env_config.get('OPENAI_BASE_URL'),
            api_key=Config.env_config.get('OPENAI_API_KEY'),
            temperature=temperature,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            seed=1000,
            http_client=Config.httpx_client
        )
    
    return OpenAIEmbeddings(
        model=model_name, 
        base_url=Config.env_config['OPENAI_BASE_URL'], 
        api_key=Config.env_config['OPENAI_API_KEY'],
        request_timeout=None,
        max_retries=2,
        http_client=Config.httpx_client
    )