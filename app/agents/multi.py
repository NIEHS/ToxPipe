from langchain_core.messages import HumanMessage

def run_parallel(self=None, input="", user_id=""):
    chain = self.agent_with_chat_history
    outputs = chain.invoke({"messages": [HumanMessage(content=input)]}, self.config,)
    outputs = outputs["messages"][-1].content # Just get last message in the chain - this is the LLM's final answer
    outputs = outputs.replace("Final Answer: ", "") # Strip "Final Answer: " if it appears in the final response
    return(outputs)