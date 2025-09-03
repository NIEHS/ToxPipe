from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

# If you are running into the cert issue
import truststore
truststore.inject_into_ssl()

# Define langfuse host and keys
langfuse = Langfuse(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    host="https://langfuse.toxpipe.niehs.nih.gov"
)

# Define langfuse handler to be added as a callback in langchain
langfuse_handler = CallbackHandler()

# Define langchain model to use
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
OPENAI_API_KEY="sk-_CVbg7aCU6GeswYMzTP_Kw"
OPENAI_BASE_URL="https://litellm.toxpipe.niehs.nih.gov"
OPENAI_API_VERSION="2024-12-01-preview"

llm = AzureChatOpenAI(
    model_name="azure-gpt-4o",
    temperature=0,
    api_version=OPENAI_API_VERSION,
    azure_endpoint=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY
)

# Define prompt and chain to call
t = """What is the molecular weight of {chemical}?"""
temp = ChatPromptTemplate.from_template(t)
chain = temp | llm

# Add handler to run/invoke/call/chat
response = chain.invoke({"chemical": "BPA"}, config={"callbacks": [langfuse_handler]})

# Print response to verify query went through properly
print(response.content)