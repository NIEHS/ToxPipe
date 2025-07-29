from langchain_openai import ChatOpenAI
from .utils import Config
from pathlib import Path

import httpx
import truststore
truststore.inject_into_ssl()
cert_path = str(Path(Config.DIR_HOME) / '.config'/ 'NIH-FULL.pem')
client = httpx.Client(verify=cert_path)

# ---------------------------------------------------------------------------
def getOpenAIModel(model_name: str, temperature: int = 0) -> ChatOpenAI:
    """
    Initializes the OpenAI Chat LLM object based on the LLM name and temperature

    :param model_name: Name of the LLM
    :param temperature: Temperature
    :return: OpenAI Chat LLM
    """
    
    return ChatOpenAI(
        model=model_name,
        base_url=Config.env_config.get('OPENAI_BASE_URL'),
        api_key=Config.env_config.get('OPENAI_API_KEY'),
        temperature=temperature,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        seed=1000,
        http_client=client
    )