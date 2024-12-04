from langgraph.errors import GraphRecursionError

def run_parallel(self=None, input="", user_id=""):
    chain = self.agent_with_chat_history
    last = ""
    try:
        for chunk in chain.stream(
            {"messages": [("human", input)]},
            self.config,
            stream_mode="values",
        ):
            last = chunk["messages"][-1].content # Just get last message in the chain - this is the LLM's final answer
    except GraphRecursionError: # Throw error if chain reaches the max number of recursions/iterations
        last = "Agent stopped due to max iterations."

    outputs = last.replace("Final Answer: ", "") # Strip "Final Answer: " if it appears in the final response

    return(outputs)