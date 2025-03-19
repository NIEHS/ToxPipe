from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from .utils import Config
from chromadb import HttpClient

# ---------------------------------------------------------------------------
class CustomRetriever():

    docs_res: dict = {}

    def __init__(self):
        embedding = OpenAIEmbeddings(
            model='text-embedding-ada-002', 
            base_url=Config.env_config['OPENAI_BASE_URL'], 
            api_key=Config.env_config['OPENAI_API_KEY']
        )
        # Local use
        #db = Chroma(collection_name='quickstart', persist_directory=str(Config.DIR_DATA), embedding_function=embedding)

        # Remote use
        chroma_client = HttpClient(host=Config.env_config['CHROMA_HOST'],  port=Config.env_config['CHROMA_PORT'])
        db = Chroma(client=chroma_client, collection_name="quickstart", embedding_function=embedding)
        self.retriever = db.as_retriever(search_type='similarity_score_threshold', search_kwargs={'k': 5, 'score_threshold': 0.3})

    def getResources(self, input):

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
                docs_str += f"\n\n** {kw} **"
                for i, d in enumerate(doc_list):
                    try:
                        docs_str += "\n\n" + ' '.join(d.page_content.strip().split()[:d_tok_est[kw][i]]) # "\n".join([f"""{d_key}: {d_val}""" for d_key, d_val in d.metadata.items()] + [d.page_content])
                    except Warning as w:
                        print(f'Resource retriever formatting: {str(w)}')

            return docs_str

        for kw in input['Keywords'][:Config.MAX_KEYWORDS]:
            try:
                docs = self.retriever.invoke(kw)
                if len(docs): self.docs_res[kw] = docs
            except Warning as w:
                print(f'Resource retriever for keyword: {kw}: {str(w)}')

        return formatResourcesFromDocs(self.docs_res)

