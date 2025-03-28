from pathlib import Path
from dotenv import dotenv_values
from langfuse.callback import CallbackHandler

from operator import add
from typing import Annotated, List

from typing_extensions import TypedDict
from langchain_core.output_parsers import JsonOutputParser

# ---------------------------------------------------------------------------
class Config:
    DIR_HOME = Path(__file__).parent.parent.parent
    DIR_DATA = (DIR_HOME / 'app' / 'rag' / 'resources')

    env_config = dotenv_values(DIR_HOME / ".config" / ".env")

    langfuse_handler = CallbackHandler(
        public_key=env_config["LANGFUSE_PUBLIC_KEY"],
        secret_key=env_config["LANGFUSE_SECRET_KEY"],
        host=env_config["LANGFUSE_HOST"]
    )

    TOKENS_PER_LLM_CALL = 5000
    MAX_KEYWORDS = 10
    MAX_NUM_DOCS = 5
    SIMILARITY_THRESHOLD = 0.3

# ---------------------------------------------------------------------------
class State(TypedDict):
    query: str
    next_action: str
    response: str
    keyphrases: List[str]
    resources: str
    steps: Annotated[List[str], add]

# ---------------------------------------------------------------------------
class OutputParser(JsonOutputParser):

    def __init__(self, output_parser):
        super().__init__(pydantic_object=output_parser)