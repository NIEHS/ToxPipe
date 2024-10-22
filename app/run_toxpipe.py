from agents import toxpipe as tp

def run_llm_query(query=""):
    tpa = tp.ToxPipeAgent(model="azure-gpt-4o", temp=0.2, max_iterations=40, n_agents=3, summarize=True, verbose=False)
    res = tpa.run(query)
    return(res)

