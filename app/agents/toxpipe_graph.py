# This is a custom, cloned implementation of LangChain's AgentExecutor so that we can modify it to better handle non-OpenAI models and for other debugging purposes.

from typing import Callable, Literal, Optional, Sequence, Type, TypeVar, Union, cast

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

from langgraph._api.deprecation import deprecated_parameter
from langgraph.errors import ErrorCode, create_error_message
from langgraph.graph import StateGraph, START, END
from langgraph.graph.graph import CompiledGraph
from langgraph.graph.message import add_messages
from langgraph.managed import IsLastStep, RemainingSteps
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.prebuilt.tool_node import ToolNode
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer
from langgraph.utils.runnable import RunnableCallable

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langgraph.graph.message import add_messages
from langchain_core.output_parsers import JsonOutputParser
from langchain.tools.render import render_text_description
from operator import itemgetter
import json
import re
import uuid

from .tools import make_translate_tools, make_rag_tools, make_literature_tools


# We create the AgentState that we will pass around
# This simply involves a list of messages
# We want steps to return messages to append to the list
# So we annotate the messages attribute with operator.add
class AgentState(TypedDict):
    """The state of the agent."""

    messages: Annotated[Sequence[BaseMessage], add_messages]

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


def _should_bind_tools(model: LanguageModelLike, tools: Sequence[BaseTool]) -> bool:
    if not isinstance(model, RunnableBinding):
        return True

    if "tools" not in model.kwargs:
        return True

    bound_tools = model.kwargs["tools"]
    if len(tools) != len(bound_tools):
        raise ValueError(
            "Number of tools in the model.bind_tools() and tools passed to create_react_agent must match"
        )

    tool_names = set(tool.name for tool in tools)
    bound_tool_names = set()
    for bound_tool in bound_tools:
        # OpenAI-style tool
        if bound_tool.get("type") == "function":
            bound_tool_name = bound_tool["function"]["name"]
        # Anthropic-style tool
        elif bound_tool.get("name"):
            bound_tool_name = bound_tool["name"]
        else:
            # unknown tool type so we'll ignore it
            continue

        bound_tool_names.add(bound_tool_name)

    if missing_tools := tool_names - bound_tool_names:
        raise ValueError(f"Missing tools '{missing_tools}' in the model.bind_tools()")

    return False


def _validate_chat_history(
    messages: Sequence[BaseMessage],
) -> None:
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
        return

    error_message = create_error_message(
        message="Found AIMessages with tool_calls that do not have a corresponding ToolMessage. "
        f"Here are the first few of those tool calls: {tool_calls_without_results[:3]}.\n\n"
        "Every tool call (LLM requesting to call a tool) in the message history MUST have a corresponding ToolMessage "
        "(result of a tool invocation to return to the LLM) - this is required by most LLM providers.",
        error_code=ErrorCode.INVALID_CHAT_HISTORY,
    )
    raise ValueError(error_message)


@deprecated_parameter("messages_modifier", "0.1.9", "state_modifier", removal="0.3.0")
def create_react_agent(
    model: LanguageModelLike,
    tools: Union[ToolExecutor, Sequence[BaseTool], ToolNode],
    *,
    state_schema: Optional[StateSchemaType] = None,
    messages_modifier: Optional[MessagesModifier] = None,
    state_modifier: Optional[StateModifier] = None,
    checkpointer: Optional[Checkpointer] = None,
    store: Optional[BaseStore] = None,
    interrupt_before: Optional[list[str]] = None,
    interrupt_after: Optional[list[str]] = None,
    manual_tool_support: Optional[list[str]] = None,
    debug: bool = False,
) -> CompiledGraph:
    """Creates a graph that works with a chat model that utilizes tool calling.

    Args:
        model: The `LangChain` chat model that supports tool calling.
        tools: A list of tools, a ToolExecutor, or a ToolNode instance.
        state_schema: An optional state schema that defines graph state.
            Must have `messages` and `is_last_step` keys.
            Defaults to `AgentState` that defines those two keys.
        messages_modifier: An optional
            messages modifier. This applies to messages BEFORE they are passed into the LLM.

            Can take a few different forms:

            - SystemMessage: this is added to the beginning of the list of messages.
            - str: This is converted to a SystemMessage and added to the beginning of the list of messages.
            - Callable: This function should take in a list of messages and the output is then passed to the language model.
            - Runnable: This runnable should take in a list of messages and the output is then passed to the language model.
            !!! Warning
                `messages_modifier` parameter is deprecated as of version 0.1.9 and will be removed in 0.2.0
        state_modifier: An optional
            state modifier. This takes full graph state BEFORE the LLM is called and prepares the input to LLM.

            Can take a few different forms:

            - SystemMessage: this is added to the beginning of the list of messages in state["messages"].
            - str: This is converted to a SystemMessage and added to the beginning of the list of messages in state["messages"].
            - Callable: This function should take in full graph state and the output is then passed to the language model.
            - Runnable: This runnable should take in full graph state and the output is then passed to the language model.
        checkpointer: An optional checkpoint saver object. This is used for persisting
            the state of the graph (e.g., as chat memory) for a single thread (e.g., a single conversation).
        store: An optional store object. This is used for persisting data
            across multiple threads (e.g., multiple conversations / users).
        interrupt_before: An optional list of node names to interrupt before.
            Should be one of the following: "agent", "tools".
            This is useful if you want to add a user confirmation or other interrupt before taking an action.
        interrupt_after: An optional list of node names to interrupt after.
            Should be one of the following: "agent", "tools".
            This is useful if you want to return directly or run additional processing on an output.
        debug: A flag indicating whether to enable debug mode.

    Returns:
        A compiled LangChain runnable that can be used for chat interactions.

    The resulting graph looks like this:

    ``` mermaid
    stateDiagram-v2
        [*] --> Start
        Start --> Agent
        Agent --> Tools : continue
        Tools --> Agent
        Agent --> End : end
        End --> [*]

        classDef startClass fill:#ffdfba;
        classDef endClass fill:#baffc9;
        classDef otherClass fill:#fad7de;

        class Start startClass
        class End endClass
        class Agent,Tools otherClass
    ```

    The "agent" node calls the language model with the messages list (after applying the messages modifier).
    If the resulting AIMessage contains `tool_calls`, the graph will then call the ["tools"][langgraph.prebuilt.tool_node.ToolNode].
    The "tools" node executes the tools (1 tool per `tool_call`) and adds the responses to the messages list
    as `ToolMessage` objects. The agent node then calls the language model again.
    The process repeats until no more `tool_calls` are present in the response.
    The agent then returns the full list of messages as a dictionary containing the key "messages".

    ``` mermaid
        sequenceDiagram
            participant U as User
            participant A as Agent (LLM)
            participant T as Tools
            U->>A: Initial input
            Note over A: Messages modifier + LLM
            loop while tool_calls present
                A->>T: Execute tools
                T-->>A: ToolMessage for each tool_calls
            end
            A->>U: Return final state
    ```
    """

    if state_schema is not None:
        if missing_keys := {"messages", "is_last_step"} - set(
            state_schema.__annotations__
        ):
            raise ValueError(f"Missing required key(s) {missing_keys} in state_schema")

    translate_tools = make_translate_tools()
    translate_tool_node = ToolNode(translate_tools)
    translate_tool_classes = list(translate_tool_node.tools_by_name.values())

    rag_tools = make_rag_tools(llm=model)
    rag_tool_node = ToolNode(rag_tools)
    rag_tool_classes = list(rag_tool_node.tools_by_name.values())

    literature_tools = make_literature_tools(llm=model)
    literature_tool_node = ToolNode(literature_tools)
    literature_tool_classes = list(literature_tool_node.tools_by_name.values())

    if isinstance(tools, ToolExecutor):
        tool_classes: Sequence[BaseTool] = tools.tools
        tool_node = ToolNode(tool_classes)
    elif isinstance(tools, ToolNode):
        tool_classes = list(tools.tools_by_name.values())
        tool_node = tools
    else:
        tool_node = ToolNode(tools)
        # get the tool functions wrapped in a tool class from the ToolNode
        tool_classes = list(tool_node.tools_by_name.values())

    #if _should_bind_tools(model, tool_classes):
        #model = cast(BaseChatModel, model).bind_tools(tool_classes)

    model_inner = model
    model_rag = model
    model_literature = model
    model_training = model

    model = cast(BaseChatModel, model).bind_tools(translate_tool_classes + rag_tool_classes + literature_tool_classes)
    model_inner = cast(BaseChatModel, model_inner).bind_tools(tool_classes)
    model_rag = cast(BaseChatModel, model_rag).bind_tools(rag_tool_classes)
    model_literature = cast(BaseChatModel, model_literature).bind_tools(literature_tool_classes)
    model_training = cast(BaseChatModel, model_literature)
    
    # Define the function that determines whether to continue or not
    def tool_calls(state: AgentState) -> Literal["tools", "agent3"]:
        messages = state["messages"]
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "agent3"
        # Otherwise if there is, we continue
        else:
            return "tools"
    
    def rag_call(state: AgentState) -> Literal["rag", "agent4"]:
        """Conduct a RAG search if unable to find an answer via the ChemBioTox tools. If this answer is unsatisfactory, then we must conduct a literature search."""
        messages = state["messages"]
        last_message = messages[-1]

        # If there is no function call, then we finish
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "agent4"
        # Otherwise if there is, we continue
        else:
            return "rag"

    def literature_call(state: AgentState) -> Literal["literature", "training"]:
        """Conduct a literature search if unable to find an answer via a RAG search. If this answer is unsatisfactory, then we must formulate an answer using the model's pretrained knowledge."""
        messages = state["messages"]
        last_message = messages[-1]

        # If there is no function call, then we finish
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "training"
        # Otherwise if there is, we continue
        else:
            return "literature"

    def training_call(state: AgentState) -> Literal["training", "__end__"]:
        """Formulate an answer using the model's pretrained knowledge. If this answer is unsatisfactory, then we must say we were unable to find an answer."""
        messages = state["messages"]
        last_message = messages[-1]

        # If there is no function call, then we finish
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "__end__"
        # Otherwise if there is, we continue
        else:
            return "training"

    # we're passing store here for validation
    preprocessor = _get_model_preprocessing_runnable(
        state_modifier, messages_modifier, store
    )

    model_runnable = preprocessor | model
    model_inner_runnable = preprocessor | model_inner
    model_rag_runnable = preprocessor | model_rag
    model_literature_runnable = preprocessor | model_literature
    model_training_runnable = preprocessor | model_training
    

    # Define the function that calls the model
    def call_model(state: AgentState, config: RunnableConfig) -> AgentState:
        _validate_chat_history(state["messages"])
        response = model_runnable.invoke(state["messages"], config)
        has_tool_calls = isinstance(response, AIMessage) and response.tool_calls
        all_tools_return_direct = (
            all(call["name"] in should_return_direct for call in response.tool_calls)
            if isinstance(response, AIMessage)
            else False
        )
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
    
    def call_model_inner(state: AgentState, config: RunnableConfig) -> AgentState:
        _validate_chat_history(state["messages"])
        response = model_inner_runnable.invoke(state["messages"], config)
        has_tool_calls = isinstance(response, AIMessage) and response.tool_calls
        all_tools_return_direct = (
            all(call["name"] in should_return_direct for call in response.tool_calls)
            if isinstance(response, AIMessage)
            else False
        )
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
    

    def call_model_rag(state: AgentState, config: RunnableConfig) -> AgentState:
        _validate_chat_history(state["messages"])
        response = model_rag_runnable.invoke(state["messages"], config)

        has_tool_calls = isinstance(response, AIMessage) and response.tool_calls
        all_tools_return_direct = (
            all(call["name"] in should_return_direct for call in response.tool_calls)
            if isinstance(response, AIMessage)
            else False
        )
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
    
    def call_model_literature(state: AgentState, config: RunnableConfig) -> AgentState:
        _validate_chat_history(state["messages"])
        response = model_literature_runnable.invoke(state["messages"], config)

        has_tool_calls = isinstance(response, AIMessage) and response.tool_calls
        all_tools_return_direct = (
            all(call["name"] in should_return_direct for call in response.tool_calls)
            if isinstance(response, AIMessage)
            else False
        )
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
    
    
    def call_model_training(state: AgentState, config: RunnableConfig) -> AgentState:
        _validate_chat_history(state["messages"])
        response = model_training_runnable.invoke(state["messages"], config)

        has_tool_calls = isinstance(response, AIMessage) and response.tool_calls
        all_tools_return_direct = (
            all(call["name"] in should_return_direct for call in response.tool_calls)
            if isinstance(response, AIMessage)
            else False
        )
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

    ### Define all nodes: ###

    ### STAGE 1 - DATA PREPROCESSING ###
    # Initial agent model node - this determines the format of the user's input - chemical name, CASRN, or SMILES
    workflow.add_node("agent", RunnableCallable(call_model))

    # Data preprocessing node - translates user input to DTXSID as that will be the standard input for all tools
    workflow.add_node("preprocess", translate_tool_node)

    ### STAGE 2 - DATA PREPROCESSING ###
    # this stage should be called up to max_iterations times
    # Stage 2 agent model node - this determines which tools, if any, to use
    workflow.add_node("agent2", RunnableCallable(call_model_inner))

    # Tool node - this is where the tools are called
    workflow.add_node("tools", tool_node)

    # Summarize node - this is where the model's output is summarized if it is excessively long
    #workflow.add_node("summarize", RunnableCallable(call_model))
    
    ### STAGE 3 - FILL IN DATA GAPS ###
    # Stage 3 agent model node - this determines how to use RAG
    workflow.add_node("agent3", RunnableCallable(call_model_rag))

    # RAG node - this is where the RAG search is conducted if the ChemBioTox tools are unable to find a satisfactory answer
    workflow.add_node("rag", rag_tool_node)
    
    # Stage 3 agent model node - this determines how to use RAG
    workflow.add_node("agent4", RunnableCallable(call_model_literature))

    # Literature node - this is where the literature search is conducted if the RAG search is unable to find a satisfactory answer
    workflow.add_node("literature", literature_tool_node)

    # Training data node - formulate a last-ditch answer from the training data if the literature search is unable to find a satisfactory answer
    workflow.add_node("training", RunnableCallable(call_model_training))


    workflow.set_entry_point("agent")

    ### ADD EDGES ###
    # Always want to start with a deliberation step to figure out how to get the user's input into DTXSID
    # Figure out which translation tool to use
    def route_preprocess_responses(state: AgentState) -> Literal["preprocess", "rag", "literature", "__end__"]:
        for m in reversed(state["messages"]):
            if not isinstance(m, ToolMessage):
                break
            if m.name in should_return_direct:
                return "__end__"
        
        #last = str(state["messages"][-1].content).lower()
        last = state["messages"][-1].tool_calls[0]["name"]

        if last == "LiteratureSearch":
            return "literature"
        elif last == "QueryRAG":
            return "rag"
        return "preprocess"
    #workflow.add_edge("agent", "preprocess")
    workflow.add_conditional_edges("agent", route_preprocess_responses)

    workflow.add_edge("preprocess", "agent2")

    # Deliberation step for tool selection - if successful, move to tools else move to RAG search
    workflow.add_conditional_edges("agent2", tool_calls)
    # After using a tool, go back to agent2 for further deliberation, summarizing if necessary
    # If any of the tools are configured to return_directly after running, our graph needs to check if these were called
    should_return_direct = {t.name for t in tool_classes if t.return_direct}
    def route_tool_responses(state: AgentState) -> Literal["agent2", "__end__"]:
        for m in reversed(state["messages"]):
            if not isinstance(m, ToolMessage):
                break
            if m.name in should_return_direct:
                return "__end__"
        return "agent2"

    if should_return_direct:
        workflow.add_conditional_edges("tools", route_tool_responses)
    else:
        workflow.add_edge("tools", "agent2")
    # TODO - add summary after tool
    #workflow.add_edge("summarize", "agent2")

    workflow.add_conditional_edges("agent3", rag_call)
    rag_should_return_direct = {t.name for t in rag_tool_classes if t.return_direct}
    def rag_route_tool_responses(state: AgentState) -> Literal["agent4", "__end__"]:
        for m in reversed(state["messages"]):
            if not isinstance(m, ToolMessage):
                break
            if m.name in should_return_direct:
                return "__end__"
        return "agent4"
    if rag_should_return_direct:
        workflow.add_conditional_edges("rag", rag_route_tool_responses)
    else:
        workflow.add_edge("rag", "agent4")


    workflow.add_conditional_edges("agent4", literature_call)
    literature_should_return_direct = {t.name for t in literature_tool_classes if t.return_direct}
    def literature_route_tool_responses(state: AgentState) -> Literal["training", "__end__"]:
        for m in reversed(state["messages"]):
            if not isinstance(m, ToolMessage):
                break
            if m.name in should_return_direct:
                return "__end__"
        return "training"
    if literature_should_return_direct:
        workflow.add_conditional_edges("literature", literature_route_tool_responses)
    else:
        workflow.add_edge("literature", "training")

    workflow.add_conditional_edges("training", training_call)
    workflow.add_edge("training", END)
    
    

    # Finally, we compile it!
    # This compiles it into a LangChain Runnable,
    # meaning you can use it as you would any other runnable
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
