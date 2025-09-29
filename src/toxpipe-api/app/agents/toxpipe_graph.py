# This is a custom, cloned implementation of LangChain's AgentExecutor so that we can modify it to better handle non-OpenAI models and for other debugging purposes.

from typing import Callable, Literal, Optional, Sequence, Type, TypeVar, Union, cast, Annotated, Any, List

from langchain_core.language_models import BaseChatModel, LanguageModelLike
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_core.runnables import (
    Runnable,
    RunnableBinding,
    RunnableConfig,
    RunnablePassthrough,
)
from langchain_core.tools import BaseTool
from typing_extensions import Annotated, TypedDict

import copy

#from langgraph._api.deprecation import deprecated_parameter
from langgraph.errors import ErrorCode, create_error_message
from langgraph.graph import StateGraph, START, END
#from langgraph.graph.graph import CompiledGraph
from langgraph.graph.message import add_messages
from langgraph.managed import IsLastStep, RemainingSteps
#from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.prebuilt.tool_node import ToolNode
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer
from langgraph.utils.runnable import RunnableCallable
from langchain_core.prompt_values import ChatPromptValue
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain_core.messages import HumanMessage, SystemMessage

from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langgraph.graph.message import add_messages
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain.tools.render import render_text_description
from operator import itemgetter
import json
from json import JSONDecodeError
from langchain_core.outputs import Generation
import re
import uuid
import itertools
from pydantic import BaseModel, Field
from langchain_core.utils.json import (
    parse_and_check_json_markdown,
    parse_json_markdown,
    parse_partial_json,
)
from .tools import make_tools, make_translate_tools, make_rag_tools, make_literature_tools, make_disease_tools, make_gene_tools
from .prompts_chem import getInnerToolsPrompt, getInnerDiseaseToolsPrompt, getInnerGeneToolsPrompt, PromptAgentic, getRepeatDiseaseToolsPrompt, getRepeatToolsPrompt, getRepeatGeneToolsPrompt

ANTHROPIC_MODELS = ['claude-3-5-sonnet', 'claude-3-sonnet', 'claude-3-haiku', 'claude-3-opus'] # haiku and opus work better
OLLAMA_MODELS = ['llama3-1-70b', 'llama3-1-8b', 'openbiollm-llama3-70b'] # These have trouble with tools
OPENAI_MODELS = ['azure-gpt-4o', 'azure-gpt-3.5-turbo', 'azure-gpt-4o-mini', 'azure-gpt-3.5-turbo-16k', 'azure-gpt-4-turbo-20240409', 'azure-gpt-4', 'azure-o1', 'azure-o1-mini', 'azure-o3-mini', 'azure-o3'] # These all work pretty well
MISTRALAI_MODELS = ['mistral-large-2', 'mistral-large', 'mistral-7b-instruct', 'mixtral-8x7b-instruct'] # mistral-large-2 and mixtral-8x7b-instruct has issues accessing tools
GOOGLE_MODELS = ['gemini-1.5-pro'] # TODO - VertexAIException BadRequestError - "Unable to submit request because one or more function parameters didn\'t specify the schema type field. Learn more: https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling
AMAZON_MODELS = ['amazon-titan-text-premier']
COHERE_MODELS = ['cohere-command-r-plus']
BAD_TOOL_MODELS = []

# Load environment variables
from dotenv import dotenv_values
from pathlib import Path
DIR_HOME = Path(__file__).parent.parent.parent
env_config = dotenv_values(DIR_HOME / ".config" / ".env")

CURRENT_DELIBERATION_STEP = 0

MAX_DELIBERATION_STEPS = int(env_config["MAX_DELIBERATION_STEPS"])

class DeliberationSchema(BaseModel):
    '''
    Represents an inner step of the agent in which it deliberates its next course of action.
    '''
    thought: str = Field(
        description="The agent's current progress and next steps to follow."
    )
    action: str = Field(
        description="The name of the next tool to use, if applicable." 
    )
    action_input: str = Field(
        description="A JSON string detailing the input for the tool, if applicable. Each key-value pair represents a parameter and its corresponding value." 
    )
    
class FinalResponseSchema(BaseModel):
    '''
    Represents the agent's final response to the user's query
    '''
    thought: str = Field(
        description="The agent's current progress and next steps to follow."
    )
    action: str = Field(
        description="The name of the next tool to use, if applicable." 
    )
    action_input: str = Field(
        description="The input for the tool, if applicable." 
    )

class FinalResponseOutputParser(StrOutputParser):
    def __init__(self, output_parser=FinalResponseSchema):
        super().__init__(pydantic_object=output_parser)

    def parseOutput(self, data):
        response = self.parse(data.content)
        return response


sufficient_system_prompt = f'''
    You are an expert toxicologist with extensive knowledge in chemical safety assessment, toxicokinetics, and toxicodynamics. Your expertise includes:

    1. Interpreting chemical structures and properties
    2. Analyzing toxicological data from various sources (e.g., in vitro, in vivo, and in silico studies)
    3. Applying read-across and QSAR (Quantitative Structure-Activity Relationship) approaches
    4. Understanding mechanisms of toxicity and adverse outcome pathways
    5. Evaluating systemic availability based on ADME (Absorption, Distribution, Metabolism, Excretion) properties
    6. Assessing potential health hazards and risks associated with chemical exposure

    When providing toxicological evaluations:
    - Use reliable scientific sources and databases (e.g., PubChem, ECHA, EPA, IARC)
    - Consider both experimental data and predictive models
    - Explain your reasoning and cite relevant studies or guidelines
    - Acknowledge uncertainties and data gaps
    - Provide a balanced assessment, considering both potential hazards and mitigating factors
    - Use a weight-of-evidence approach when multiple data sources are available
    - Classify toxicodynamic activity and systemic availability as high, medium, or low based on 
    the available evidence and expert judgment
    - When using read-across, clearly state the basis for the analogy and any limitations

    Adhere to ethical standards in toxicology and maintain scientific objectivity in your assessments.
    '''

sufficient_human_prompt = '''
You will be provided with the most recent response from the model and the user's original query. Please review the response and determine if it is sufficient to answer the original query. If the response is sufficient, please respond with "sufficient". If the response is not sufficient, please respond with "not sufficient". Do not respond with anything else.
- If the response could benefit from using the tools available, please respond with "not sufficient" so the model can use the tools to find a more accurate answer.
- If the user specifically asks to perform a search on available literature or the RAG model, please respond with "not sufficient" so the model can perform the search.
- If the user specifically asks to use the model's training data, please respond with "not sufficient" so the model can use its training data.
- If a RAG search comes to an irrelevant decision, please respond with "not sufficient" so the model can use its training data to find a more accurate answer.
- If a literature search cannot find information, please respond with "not sufficient" so the model can use its training data to find a more accurate answer.

----------------------------------------------
**Response**
{response}

----------------------------------------------
**Query**
{query}

----------------------------------------------
**Possible Tools**
{tools}

**Output format**
You will always output either "sufficient" or "not sufficient" based on your decision.
'''


sufficient_prompt = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            (sufficient_system_prompt),
        ),
        (
            'human',
            (sufficient_human_prompt),
        ),
    ]
)


training_human_prompt = '''
**Instructions**
- Review the provided context to determine if it adequately addresses the user's query.
- You must generate a final answer using both your training data and relevant parts of the provided context that are relevant to the user's query.
- You must always supplement the context with a thorough answer from your training data.

**Output format**
Your output must follow the following rules and format UNLESS the user's query specifies a different format. If the user's query specifies a different format, you must follow the format specified in the user's query.
- Final Answer: (the final answer to the original input question after using the appropriate tools. You must include sources for each section of the information provided.
- When sourcing information from ChemBioTox, you must specify which datasource in ChemBioTox was used (for example, CTD, PubChem, EPA, DrugBank, etc.).
- Do not include any "Thought:" in your final answer. Only return the information following "Final Answer:".
- Important: the entire final answer must not exceed 2 paragraphs (around 2000-3000 characters). Summarize the data if necessary to meet this requirement, but make sure to retain important and specific information relevant to the original query.
- Unless specified otherwise, do not answer in JSON format.

----------------------------------------------
**Context**
{context}

----------------------------------------------
**Original Query**
{query}


'''

training_prompt = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            (sufficient_system_prompt),
        ),
        (
            'human',
            (training_human_prompt),
        ),
    ]
)



force_rag_prompt = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            (sufficient_system_prompt),
        ),
        (
            'human',
            (
                """
                    Below is the user's query. You must format the user's original query into a concise query to be used with the QueryRAG tool, then you must call the QueryRAG tool using this new query as input.
                    
                    ** User's Query **
                    {query}
                """
            ),
        ),
    ]
)

force_literature_prompt = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            (sufficient_system_prompt),
        ),
        (
            'human',
            (
                """
                    Below is the user's query. You must format the user's original query into a concise query to be used with the LiteratureSearch tool, then you must call the LiteratureSearch tool using this new query as input.
                    
                    ** User's Query **
                    {query}
                """
            ),
        ),
    ]
)

# We create the AgentState that we will pass around
# This simply involves a list of messages
# We want steps to return messages to append to the list
# So we annotate the messages attribute with operator.add
class AgentState(TypedDict):
    """The state of the agent."""

    messages: Annotated[Sequence[BaseMessage], add_messages]

    tools_handler_messages: Annotated[Sequence[BaseMessage], add_messages]

    rag_handler_messages: Annotated[Sequence[BaseMessage], add_messages]

    literature_handler_messages: Annotated[Sequence[BaseMessage], add_messages]

    is_last_step: IsLastStep

    remaining_steps: RemainingSteps


StateSchema = TypeVar("StateSchema", bound=AgentState)
StateSchemaType = Type[StateSchema]

STATE_MODIFIER_RUNNABLE_NAME = "StateModifier"

MessagesModifier = Union[
    SystemMessage,
    str,
    Callable[[Sequence[BaseMessage]], Sequence[BaseMessage]],
    Runnable[Sequence[BaseMessage], Sequence[BaseMessage]],
]

StateModifier = Union[
    SystemMessage,
    str,
    Callable[[StateSchema], Sequence[BaseMessage]],
    Runnable[StateSchema, Sequence[BaseMessage]],
]


def _get_state_modifier_runnable(
    state_modifier: Optional[StateModifier], store: Optional[BaseStore] = None
) -> Runnable:
    state_modifier_runnable: Runnable
    if state_modifier is None:
        state_modifier_runnable = RunnableCallable(
            lambda state: state["messages"], name=STATE_MODIFIER_RUNNABLE_NAME
        )
    elif isinstance(state_modifier, str):
        _system_message: BaseMessage = SystemMessage(content=state_modifier)
        state_modifier_runnable = RunnableCallable(
            lambda state: [_system_message] + state["messages"],
            name=STATE_MODIFIER_RUNNABLE_NAME,
        )
    elif isinstance(state_modifier, SystemMessage):
        state_modifier_runnable = RunnableCallable(
            lambda state: [state_modifier] + state["messages"],
            name=STATE_MODIFIER_RUNNABLE_NAME,
        )
    elif callable(state_modifier):
        state_modifier_runnable = RunnableCallable(
            state_modifier,
            name=STATE_MODIFIER_RUNNABLE_NAME,
        )
    elif isinstance(state_modifier, Runnable):
        state_modifier_runnable = state_modifier
    else:
        raise ValueError(
            f"Got unexpected type for `state_modifier`: {type(state_modifier)}"
        )

    return state_modifier_runnable


def _convert_messages_modifier_to_state_modifier(
    messages_modifier: MessagesModifier,
) -> StateModifier:
    state_modifier: StateModifier
    if isinstance(messages_modifier, (str, SystemMessage)):
        return messages_modifier
    elif callable(messages_modifier):

        def state_modifier(state: AgentState) -> Sequence[BaseMessage]:
            return messages_modifier(state["messages"])

        return state_modifier
    elif isinstance(messages_modifier, Runnable):
        state_modifier = (lambda state: state["messages"]) | messages_modifier
        return state_modifier
    raise ValueError(
        f"Got unexpected type for `messages_modifier`: {type(messages_modifier)}"
    )


def _get_model_preprocessing_runnable(
    state_modifier: Optional[StateModifier],
    messages_modifier: Optional[MessagesModifier],
    store: Optional[BaseStore],
) -> Runnable:
    # Add the state or message modifier, if exists
    if state_modifier is not None and messages_modifier is not None:
        raise ValueError(
            "Expected value for either state_modifier or messages_modifier, got values for both"
        )

    if state_modifier is None and messages_modifier is not None:
        state_modifier = _convert_messages_modifier_to_state_modifier(messages_modifier)

    return _get_state_modifier_runnable(state_modifier, store)


def _validate_chat_history(
    messages: Sequence[BaseMessage],
) -> Sequence[BaseMessage]:
    """Validate that all tool calls in AIMessages have a corresponding ToolMessage."""
    all_tool_calls = [
        tool_call
        for message in messages
        if isinstance(message, AIMessage)
        for tool_call in message.tool_calls
    ]
    tool_call_ids_with_results = {
        message.tool_call_id for message in messages if isinstance(message, ToolMessage)
    }
    tool_calls_without_results = [
        tool_call
        for tool_call in all_tool_calls
        if tool_call["id"] not in tool_call_ids_with_results
    ]

    if not tool_calls_without_results:
        return messages
    
    # Prune any messages from the history that don't have a corresponding tool call
    pruned_messages = []
    for message in messages:
        if isinstance(message, ToolMessage) and message.tool_call_id not in tool_call_ids_with_results:
            continue
        elif isinstance(message, AIMessage):
            if message.tool_calls:
                ids = [call["id"] for call in message.tool_calls]
                bad_ids = [id for id in ids if id not in tool_call_ids_with_results]
                if len(bad_ids) > 0:
                    continue
                else:
                    pruned_messages.append(message)
            else:
                pruned_messages.append(message)
        else:
            pruned_messages.append(message)
    messages = pruned_messages
    return messages


def create_react_agent(
    model: LanguageModelLike,
    tools: Union[Sequence[BaseTool], ToolNode],
    *,
    state_schema: Optional[StateSchemaType] = None,
    messages_modifier: Optional[MessagesModifier] = None,
    state_modifier: Optional[StateModifier] = None,
    checkpointer: Optional[Checkpointer] = None,
    store: Optional[BaseStore] = None,
    interrupt_before: Optional[list[str]] = None,
    interrupt_after: Optional[list[str]] = None,
    debug: bool = False,
    model_name: Optional[str] = None,
    max_memory_tokens: Optional[int] = 0
):

    if state_schema is not None:
        if missing_keys := {"messages", "is_last_step"} - set(
            state_schema.__annotations__
        ):
            raise ValueError(f"Missing required key(s) {missing_keys} in state_schema")

    translate_tools = make_translate_tools(llm=model)
    translate_tool_node = ToolNode(translate_tools, messages_key="messages")
    translate_tool_classes = list(translate_tool_node.tools_by_name.values())
    translate_tool_names = list(translate_tool_node.tools_by_name.keys())

    rag_tools = make_rag_tools(llm=model)
    rag_tool_node = ToolNode(rag_tools, messages_key="messages")
    rag_tool_classes = list(rag_tool_node.tools_by_name.values())
    rag_tool_names = list(rag_tool_node.tools_by_name.keys())

    literature_tools = make_literature_tools(llm=model)
    literature_tool_node = ToolNode(literature_tools, messages_key="messages")
    literature_tool_classes = list(literature_tool_node.tools_by_name.values())
    literature_tool_names = list(literature_tool_node.tools_by_name.keys())

    disease_tools = make_disease_tools(llm=model)
    disease_tool_node = ToolNode(disease_tools, messages_key="messages")
    disease_tool_classes = list(disease_tool_node.tools_by_name.values())
    disease_tool_names = list(disease_tool_node.tools_by_name.keys())
    
    gene_tools = make_gene_tools(llm=model)
    gene_tool_node = ToolNode(gene_tools, messages_key="messages")
    gene_tool_classes = list(gene_tool_node.tools_by_name.values())
    gene_tool_names = list(gene_tool_node.tools_by_name.keys())

    #tool_node = ToolNode(tools, messages_key="tools_handler_messages")
    #tool_classes = list(tool_node.tools_by_name.values())
    #tool_names = list(tool_node.tools_by_name.keys())

    tool_node = ToolNode(translate_tools + tools + rag_tools + literature_tools + gene_tools + disease_tools, messages_key="messages")
    tool_classes = list(tool_node.tools_by_name.values())
    tool_names = list(tool_node.tools_by_name.keys())

    llm = model

    model_start = cast(BaseChatModel, model).bind_tools(translate_tool_classes + tool_classes + rag_tool_classes + literature_tool_classes + gene_tool_classes + disease_tool_classes, tool_choice="any")
    model_inner = cast(BaseChatModel, model).bind_tools(tool_classes, tool_choice="any")
    model_repeat = cast(BaseChatModel, model).bind_tools(tool_classes)
    model_disease_inner = cast(BaseChatModel, model).bind_tools(disease_tool_classes, tool_choice="any")
    model_disease_repeat = cast(BaseChatModel, model).bind_tools(disease_tool_classes + translate_tool_classes)

    model_gene_inner = cast(BaseChatModel, model).bind_tools(gene_tool_classes, tool_choice="any")
    model_gene_repeat = cast(BaseChatModel, model).bind_tools(gene_tool_classes + translate_tool_classes)

    model_training = cast(BaseChatModel, model)

    model_force_rag = cast(BaseChatModel, model).bind_tools(rag_tool_classes, tool_choice="QueryRAG")
    model_force_literature = cast(BaseChatModel, model).bind_tools(literature_tool_classes, tool_choice="LiteratureSearch")

    # Truncate context window if too long
    def condense_prompt(prompt: ChatPromptValue) -> ChatPromptValue:        
        messages = prompt.to_messages()
        num_tokens = llm.get_num_tokens_from_messages(messages)
        ai_function_messages = messages[2:]

        if max_memory_tokens > 0: # When 0, don't trim the context window
            while num_tokens > max_memory_tokens:
                ai_function_messages = ai_function_messages[2:]
                num_tokens = llm.get_num_tokens_from_messages(
                    messages[:2] + ai_function_messages
                )
        messages = messages[:2] + ai_function_messages # append the first two messages (system and human) to the trimmed list of internal messages

        # Prune any tool messages without a tool call
        tool_messages = [message.tool_call_id for message in messages if isinstance(message, ToolMessage)]
        tool_call_messages = [[i['id'] for i in message.tool_calls] for message in messages if isinstance(message, AIMessage) and message.tool_calls]
        tool_call_messages = list(itertools.chain.from_iterable(tool_call_messages)) # flatten the list of tool call messages
        good_tool_calls = list(set(tool_messages) & set(tool_call_messages)) # get only tool calls that have a corresponding tool message
        pruned_messages = []
        for message in messages:
            if isinstance(message, ToolMessage) and message.tool_call_id not in good_tool_calls:
                continue
            elif isinstance(message, AIMessage):
                if message.tool_calls:
                    ids = [call["id"] for call in message.tool_calls]
                    bad_ids = [id for id in ids if id not in good_tool_calls]
                    if len(bad_ids) > 0:
                        continue
                    else:
                        pruned_messages.append(message)
                else:
                    pruned_messages.append(message)
            else:
                pruned_messages.append(message)
        messages = pruned_messages
        return ChatPromptValue(messages=messages)

    # we're passing store here for validation
    preprocessor = _get_model_preprocessing_runnable(
        state_modifier, messages_modifier, store
    )
    
    tools_prompt = getInnerToolsPrompt(PromptAgentic)
    inner_preprocessor = _get_model_preprocessing_runnable(
        tools_prompt, messages_modifier, store
    )

    repeat_prompt = getRepeatToolsPrompt(PromptAgentic)
    repeat_preprocessor = _get_model_preprocessing_runnable(
        repeat_prompt, messages_modifier, store
    )

    disease_tools_prompt = getInnerDiseaseToolsPrompt(PromptAgentic)
    disease_inner_preprocessor = _get_model_preprocessing_runnable(
        disease_tools_prompt, messages_modifier, store
    )

    disease_repeat_prompt = getRepeatDiseaseToolsPrompt(PromptAgentic)
    disease_repeat_preprocessor = _get_model_preprocessing_runnable(
        disease_repeat_prompt, messages_modifier, store
    )

    gene_tools_prompt = getInnerGeneToolsPrompt(PromptAgentic)
    gene_inner_preprocessor = _get_model_preprocessing_runnable(
        gene_tools_prompt, messages_modifier, store
    )

    gene_repeat_prompt = getRepeatGeneToolsPrompt(PromptAgentic)
    gene_repeat_preprocessor = _get_model_preprocessing_runnable(
        gene_repeat_prompt, messages_modifier, store
    )

    
    model_start_runnable = preprocessor | condense_prompt | model_start
    model_inner_runnable = inner_preprocessor | condense_prompt | model_inner
    model_repeat_runnable = repeat_preprocessor | condense_prompt | model_repeat
    model_disease_inner_runnable = disease_inner_preprocessor | condense_prompt | model_disease_inner
    model_disease_repeat_runnable = disease_repeat_preprocessor | condense_prompt | model_disease_repeat
    model_gene_inner_runnable = gene_inner_preprocessor | condense_prompt | model_gene_inner
    model_gene_repeat_runnable = gene_repeat_preprocessor | condense_prompt | model_gene_repeat
    model_training_runnable = training_prompt | model_training

    model_force_rag_runnable = force_rag_prompt | model_force_rag
    model_force_literature_runnable = force_literature_prompt | model_force_literature

    def call_start(state: AgentState, config: RunnableConfig) -> AgentState:
        global CURRENT_DELIBERATION_STEP
        CURRENT_DELIBERATION_STEP = 0
        return state
    


    # Define the function that calls the model
    def call_model(state: AgentState, config: RunnableConfig) -> AgentState:
        global CURRENT_DELIBERATION_STEP
        CURRENT_DELIBERATION_STEP = CURRENT_DELIBERATION_STEP + 1

        state["messages"] = _validate_chat_history(state["messages"])

        # Clear individual history for each handler
        state["tools_handler_messages"] = []
        #state["rag_handler_messages"] = []
        #state["literature_handler_messages"] = []

        

        response = model_start_runnable.invoke(state["messages"], config=config) # Generate tool calls

        has_tool_calls = isinstance(response, AIMessage) and response.tool_calls

        translation_messages = copy.deepcopy(response)

        """
        # Force RAG/lit tool calls
        user_query = [message for message in state["messages"] if isinstance(message, HumanMessage)][-1]
        first_tool_calls = [call['name'] for call in response.tool_calls]
        if 'QueryRAG' not in first_tool_calls:
            force_rag_resp = model_force_rag_runnable.invoke({"query": user_query}, config)
            rag_messages = copy.deepcopy(force_rag_resp)
        else:
            rag_messages = copy.deepcopy(response)

        if 'LiteratureSearch' not in first_tool_calls:
            force_literature_resp = model_force_literature_runnable.invoke({"query": user_query}, config)
            literature_messages = copy.deepcopy(force_literature_resp)
        else:
            literature_messages = copy.deepcopy(response)

        """

        if has_tool_calls:

            all_tools_return_direct = False
            if (
                (
                    "remaining_steps" not in state
                    and state["is_last_step"]
                    and has_tool_calls
                )
                or (
                    "remaining_steps" in state
                    and state["remaining_steps"] < 1
                    and all_tools_return_direct
                )
                or (
                    "remaining_steps" in state
                    and state["remaining_steps"] < 2
                    and has_tool_calls
                )
            ):
                return {
                    "messages": [
                        AIMessage(
                            id=response.id,
                            content="Sorry, need more steps to process this request.",
                        )
                    ]
                }

            """
            # Parse out translation tool calls
            translation_messages.additional_kwargs = {
                "tool_calls": [call for call in response.additional_kwargs["tool_calls"] if call["function"]["name"] in translate_tool_names],
                "type": "function"
            }
            translation_messages.tool_calls = [call for call in response.tool_calls if call["name"] in translate_tool_names]

            
            # Parse out rag tool calls
            rag_messages.additional_kwargs = {
                "tool_calls": [call for call in rag_messages.additional_kwargs["tool_calls"] if call["function"]["name"] in rag_tool_names],
                "type": "function"
            }
            rag_messages.tool_calls = [call for call in rag_messages.tool_calls if call["name"] in rag_tool_names]
            
            # Parse out literature tool calls
            literature_messages.additional_kwargs = {
                "tool_calls": [call for call in literature_messages.additional_kwargs["tool_calls"] if call["function"]["name"] in literature_tool_names],
                "type": "function"
            }
            literature_messages.tool_calls = [call for call in literature_messages.tool_calls if call["name"] in literature_tool_names]
            """

            return {
                "messages": [response],
                #"tools_handler_messages": [translation_messages],
                #"rag_handler_messages": [rag_messages],
                #"literature_handler_messages": [literature_messages]
            }
        
        else:
            return {
                "messages": [response],
                "tools_handler_messages": [],
                #"rag_handler_messages": [],
                #"literature_handler_messages": []
            }
        
    # Define the function that calls the model
    def call_skip(state: AgentState, config: RunnableConfig) -> AgentState:
        return state
    
    def call_disease(state: AgentState, config: RunnableConfig) -> AgentState:
        return state
    
    def call_gene(state: AgentState, config: RunnableConfig) -> AgentState:
        return state
    
    def call_tools_capture(state: AgentState, config: RunnableConfig) -> AgentState:
        return state
  
    def call_model_inner(state: AgentState, config: RunnableConfig) -> AgentState:

        state["tools_handler_messages"] = _validate_chat_history(state["tools_handler_messages"])

        if isinstance(state["tools_handler_messages"][-1], ToolMessage):
            try:
                user_query = [message for message in state["messages"] if isinstance(message, HumanMessage)][-1]

                dtxsid = [message for message in state["tools_handler_messages"] if isinstance(message, ToolMessage)]
                
                
                response = model_inner_runnable.invoke({"query": user_query, "dtxsid": dtxsid, "tools": tool_names, "messages": state["tools_handler_messages"]}, config=config) # Generate tool calls

                has_tool_calls = isinstance(response, AIMessage) and response.tool_calls

                all_tools_return_direct = False
                if (
                    (
                        "remaining_steps" not in state
                        and state["is_last_step"]
                        and has_tool_calls
                    )
                    or (
                        "remaining_steps" in state
                        and state["remaining_steps"] < 1
                        and all_tools_return_direct
                    )
                    or (
                        "remaining_steps" in state
                        and state["remaining_steps"] < 2
                        and has_tool_calls
                    )
                ):
                    return {
                        "tools_handler_messages": [
                            AIMessage(
                                id=response.id,
                                content="Sorry, need more steps to process this request.",
                            )
                        ]
                    }
                return {"tools_handler_messages": [response]} 
            
            except:
                return {
                    "tools_handler_messages": [],
                }


        return {
            "tools_handler_messages": [],
        }
    
    def call_disease_inner(state: AgentState, config: RunnableConfig) -> AgentState:

        state["tools_handler_messages"] = _validate_chat_history(state["tools_handler_messages"])

        if isinstance(state["tools_handler_messages"][-1], ToolMessage):
            try:
            
                user_query = [message for message in state["messages"] if isinstance(message, HumanMessage)][-1]

                disease_name = [message for message in state["tools_handler_messages"] if isinstance(message, ToolMessage)]

                
                response = model_disease_inner_runnable.invoke({"query": user_query, "name": disease_name, "tools": disease_tool_names, "messages": state["tools_handler_messages"]}, config=config) # Generate tool calls

                has_tool_calls = isinstance(response, AIMessage) and response.tool_calls

                all_tools_return_direct = False
                if (
                    (
                        "remaining_steps" not in state
                        and state["is_last_step"]
                        and has_tool_calls
                    )
                    or (
                        "remaining_steps" in state
                        and state["remaining_steps"] < 1
                        and all_tools_return_direct
                    )
                    or (
                        "remaining_steps" in state
                        and state["remaining_steps"] < 2
                        and has_tool_calls
                    )
                ):
                    return {
                        "tools_handler_messages": [
                            AIMessage(
                                id=response.id,
                                content="Sorry, need more steps to process this request.",
                            )
                        ]
                    }
                return {"tools_handler_messages": [response]} 
            
            except:
                return {
                    "tools_handler_messages": [],
                }


        return {
            "tools_handler_messages": [],
        }

    def call_model_disease_repeat(state: AgentState, config: RunnableConfig) -> AgentState:
        state["tools_handler_messages"] = _validate_chat_history(state["tools_handler_messages"])
        if isinstance(state["tools_handler_messages"][-1], ToolMessage):
            try:
                user_query = [message for message in state["messages"] if isinstance(message, HumanMessage)][-1]

                
                response = model_disease_repeat_runnable.invoke({"query": user_query, "tools": disease_tool_names + translate_tool_names, "messages": state["tools_handler_messages"]}, config=config) # Generate tool calls

                has_tool_calls = isinstance(response, AIMessage) and response.tool_calls
                all_tools_return_direct = False
                if (
                    (
                        "remaining_steps" not in state
                        and state["is_last_step"]
                        and has_tool_calls
                    )
                    or (
                        "remaining_steps" in state
                        and state["remaining_steps"] < 1
                        and all_tools_return_direct
                    )
                    or (
                        "remaining_steps" in state
                        and state["remaining_steps"] < 2
                        and has_tool_calls
                    )
                ):
                    return {
                        "tools_handler_messages": [
                            AIMessage(
                                id=response.id,
                                content="Sorry, need more steps to process this request.",
                            )
                        ]
                    }
                return {"tools_handler_messages": [response]} 
            
            except Exception as e:
                return {
                    "tools_handler_messages": [],
                }

        return {
            "tools_handler_messages": [],
        }
    

    def call_gene_inner(state: AgentState, config: RunnableConfig) -> AgentState:

        state["tools_handler_messages"] = _validate_chat_history(state["tools_handler_messages"])

        if isinstance(state["tools_handler_messages"][-1], ToolMessage):
            try:
            
                user_query = [message for message in state["messages"] if isinstance(message, HumanMessage)][-1]

                gene_name = [message for message in state["tools_handler_messages"] if isinstance(message, ToolMessage)]

                
                response = model_gene_inner_runnable.invoke({"query": user_query, "name": gene_name, "tools": gene_tool_names, "messages": state["tools_handler_messages"]}, config=config) # Generate tool calls

                has_tool_calls = isinstance(response, AIMessage) and response.tool_calls

                all_tools_return_direct = False
                if (
                    (
                        "remaining_steps" not in state
                        and state["is_last_step"]
                        and has_tool_calls
                    )
                    or (
                        "remaining_steps" in state
                        and state["remaining_steps"] < 1
                        and all_tools_return_direct
                    )
                    or (
                        "remaining_steps" in state
                        and state["remaining_steps"] < 2
                        and has_tool_calls
                    )
                ):
                    return {
                        "tools_handler_messages": [
                            AIMessage(
                                id=response.id,
                                content="Sorry, need more steps to process this request.",
                            )
                        ]
                    }
                return {"tools_handler_messages": [response]} 
            
            except:
                return {
                    "tools_handler_messages": [],
                }

        return {
            "tools_handler_messages": [],
        }
    

    def call_model_gene_repeat(state: AgentState, config: RunnableConfig) -> AgentState:
        state["tools_handler_messages"] = _validate_chat_history(state["tools_handler_messages"])
        if isinstance(state["tools_handler_messages"][-1], ToolMessage):
            try:
                user_query = [message for message in state["messages"] if isinstance(message, HumanMessage)][-1]

                
                response = model_gene_repeat_runnable.invoke({"query": user_query, "tools": gene_tool_names + translate_tool_names, "messages": state["tools_handler_messages"]}, config=config) # Generate tool calls

                has_tool_calls = isinstance(response, AIMessage) and response.tool_calls
                all_tools_return_direct = False
                if (
                    (
                        "remaining_steps" not in state
                        and state["is_last_step"]
                        and has_tool_calls
                    )
                    or (
                        "remaining_steps" in state
                        and state["remaining_steps"] < 1
                        and all_tools_return_direct
                    )
                    or (
                        "remaining_steps" in state
                        and state["remaining_steps"] < 2
                        and has_tool_calls
                    )
                ):
                    return {
                        "tools_handler_messages": [
                            AIMessage(
                                id=response.id,
                                content="Sorry, need more steps to process this request.",
                            )
                        ]
                    }
                return {"tools_handler_messages": [response]} 
            
            except Exception as e:
                return {
                    "tools_handler_messages": [],
                }

        return {
            "tools_handler_messages": [],
        }
    

    def call_model_repeat(state: AgentState, config: RunnableConfig) -> AgentState:
        state["tools_handler_messages"] = _validate_chat_history(state["tools_handler_messages"])
        if isinstance(state["tools_handler_messages"][-1], ToolMessage):
            try:
                user_query = [message for message in state["messages"] if isinstance(message, HumanMessage)][-1]

                
                response = model_repeat_runnable.invoke({"query": user_query, "tools": tool_names, "messages": state["tools_handler_messages"]}, config=config) # Generate tool calls

                has_tool_calls = isinstance(response, AIMessage) and response.tool_calls
                all_tools_return_direct = False
                if (
                    (
                        "remaining_steps" not in state
                        and state["is_last_step"]
                        and has_tool_calls
                    )
                    or (
                        "remaining_steps" in state
                        and state["remaining_steps"] < 1
                        and all_tools_return_direct
                    )
                    or (
                        "remaining_steps" in state
                        and state["remaining_steps"] < 2
                        and has_tool_calls
                    )
                ):
                    return {
                        "tools_handler_messages": [
                            AIMessage(
                                id=response.id,
                                content="Sorry, need more steps to process this request.",
                            )
                        ]
                    }
                return {"tools_handler_messages": [response]} 
            
            except Exception as e:
                return {
                    "tools_handler_messages": [],
                }

        return {
            "tools_handler_messages": [],
        }
    
    def call_model_training(state: AgentState, config: RunnableConfig) -> AgentState:
        # Merge message histories from all handlers
        state["messages"] = state["messages"]
        state["messages"] = _validate_chat_history(state["messages"])
        user_query = [message for message in state["messages"] if isinstance(message, HumanMessage)][-1]#.content
        context = [message for message in state["messages"] if isinstance(message, ToolMessage)]
        
        response = model_training_runnable.invoke({"context": context, "query": user_query}, config=config) # Final answer from training data and context
        has_tool_calls = isinstance(response, AIMessage) and response.tool_calls
        all_tools_return_direct = False
        if (
            (
                "remaining_steps" not in state
                and state["is_last_step"]
                and has_tool_calls
            )
            or (
                "remaining_steps" in state
                and state["remaining_steps"] < 1
                and all_tools_return_direct
            )
            or (
                "remaining_steps" in state
                and state["remaining_steps"] < 2
                and has_tool_calls
            )
        ):
            return {
                "messages": [
                    AIMessage(
                        id=response.id,
                        content="Sorry, need more steps to process this request.",
                    )
                ]
            }
        # We return a list, because this will get added to the existing list
        return {"messages": [response]} 


    

    # Define a new graph
    workflow = StateGraph(state_schema or AgentState)
    
    workflow.add_node("START_NODE", RunnableCallable(call_start))
    workflow.add_node("DELIBERATION_NODE", RunnableCallable(call_model))
    workflow.add_node("TOOL_NODE", tool_node)
    workflow.add_node("SUMMARY_NODE", RunnableCallable(call_model_training))

    workflow.add_edge(START, "START_NODE") # Start with the agent node

    workflow.add_edge("START_NODE", "DELIBERATION_NODE") # Start with the agent node
    
    def can_repeat_tools(state: AgentState) -> Literal["TOOL_NODE", "SUMMARY_NODE"]:
        messages = state["messages"]
        last_message = messages[-1]

        global CURRENT_DELIBERATION_STEP
        CURRENT_DELIBERATION_STEP = CURRENT_DELIBERATION_STEP # This is just so the Python linter doesn't complain

        if CURRENT_DELIBERATION_STEP > MAX_DELIBERATION_STEPS:
            return "SUMMARY_NODE"

        if hasattr(last_message, "tool_calls"):
            return "TOOL_NODE"
        else:
            return "SUMMARY_NODE"
    workflow.add_conditional_edges("DELIBERATION_NODE", can_repeat_tools) # Once we have the DTXSID, we can call the tools
    
    workflow.add_edge("TOOL_NODE", "DELIBERATION_NODE")

    # Compile graph
    workflow = workflow.compile(
        checkpointer=checkpointer,
        store=store,
        interrupt_before=interrupt_before,
        interrupt_after=interrupt_after,
        debug=debug,
    )
    return workflow 


# Keep for backwards compatibility
create_tool_calling_executor = create_react_agent

__all__ = [
    "create_react_agent",
    "create_tool_calling_executor",
    "AgentState",
]
