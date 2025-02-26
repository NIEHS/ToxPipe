from langchain_openai import ChatOpenAI
from .utils import Config
from dotenv import dotenv_values, load_dotenv
import os
load_dotenv('../../.config/.env')

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
        base_url=os.environ.get('OPENAI_BASE_URL'),
        api_key=os.environ.get('OPENAI_API_KEY'),
        temperature=temperature,
        max_tokens=None,
        timeout=None,
        max_retries=10,
        seed=1000
    )