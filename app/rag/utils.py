from pathlib import Path
from dotenv import dotenv_values
from langfuse.callback import CallbackHandler

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