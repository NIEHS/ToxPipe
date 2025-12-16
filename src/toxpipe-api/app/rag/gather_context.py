from langchain_chroma import Chroma
from chromadb import HttpClient
from .utils import Config, State
from .llms import getAIModel

# ---------------------------------------------------------------------------
class CustomRetriever():

    docs_res: dict = {}

    def __init__(self):
        embedding = getAIModel(model_name='text-embedding-ada-002', is_embedding=True)

        # Local use
        #db = Chroma(collection_name='quickstart', persist_directory=str(Config.DIR_DATA), embedding_function=embedding)

        # Remote use
        chroma_client = HttpClient(host=Config.env_config['CHROMA_HOST'],  port=Config.env_config['CHROMA_PORT'])
        db = Chroma(client=chroma_client, collection_name='quickstart', embedding_function=embedding)
        
        self.retriever = db.as_retriever(search_type='similarity_score_threshold', search_kwargs={'k': Config.MAX_NUM_DOCS, 'score_threshold': Config.SIMILARITY_THRESHOLD})

    def getResources(self, keyphrases):

        def formatResourcesFromDocs(docs):
            
            def estimateTokenLimits(docs):

                est = []
            
                for kw, doc_list in docs.items():
                    est += [[len(d.page_content.strip().split()), kw, i] for i, d in enumerate(doc_list)]

                est = sorted(est)
                
                d_tok_est = {}
                token_limit = Config.TOKENS_PER_LLM_CALL
                for j, (s, k, i) in enumerate(est):
                    d_tok_est[k] = {**d_tok_est.get(k, {}), **{i: 0}}
                    d_tok_est[k][i] = min(s, token_limit//(len(est)-j))
                    token_limit -= d_tok_est[k][i]

                return d_tok_est

            d_tok_est = estimateTokenLimits(docs)

            docs_str = ''
            for kw, doc_list in docs.items():
                docs_str += f'\n\n** {kw} **'
                for i, d in enumerate(doc_list):
                    try:
                        docs_str += '\n\n' + ' '.join(d.page_content.strip().split()[:d_tok_est[kw][i]]) # '\n'.join([f'''{d_key}: {d_val}''' for d_key, d_val in d.metadata.items()] + [d.page_content])
                    except Warning as w:
                        print(f'Resource retriever formatting: {str(w)}')

            return docs_str
        
        self.docs_res = {}
        for kw in keyphrases[:Config.MAX_KEYPHRASES]:
            try:
                docs = self.retriever.invoke(kw)
                if len(docs): self.docs_res[kw] = docs
            except Warning as w:
                print(f'Resource retriever for keyword: {kw}: {str(w)}')

        return formatResourcesFromDocs(self.docs_res)

# ---------------------------------------------------------------------------
class GatherContext:
    
    def __init__(self):
        self.retriever = CustomRetriever()

    def gather_context(self, state: State) -> State:
        '''
        Gather context using keyphrases extracted from user query
        '''

        resources = self.retriever.getResources(state.get('keyphrases'))
        
        return {'resources': resources, 
                'steps': ['gather_context']}