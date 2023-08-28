from elasticsearch import Elasticsearch
import os 
from langchain.embeddings import HuggingFaceEmbeddings, SentenceTransformerEmbeddings
from langchain.vectorstores import ElasticVectorSearch
from langchain.document_loaders import OnlinePDFLoader
from langchain.text_splitter import CharacterTextSplitter
#es_connection = Elasticsearch(hosts=["elasticsearch://elasticsearch:9200"], basic_auth=(os.environ['ELASTIC_USERNAME'], os.environ['ELASTIC_PASSWORD']))
#print(es_connection.info())


from opensearchpy import OpenSearch

host = 'opensearch'
port = 9200
auth = ('admin', 'admin') # For testing only. Don't store credentials in code.

client = OpenSearch(
    hosts = [{'host': host, 'port': port}],
    
)

info = client.info()
print(f"Welcome to {info['version']['distribution']} {info['version']['number']}!")


# Create indicies
settings = {
    "settings": {
        "index": {
            "knn": True,
        }
    },
    "mappings": {
        "properties": {
            "name": {"type": "text"},
            "id": {"type": "integer"},
            "description": {"type": "text"},
            "embedding": {
                "type": "knn_vector",
                "dimension": 384,
            },
        }
    },
}

model_name = "sentence-transformers/all-mpnet-base-v2"
hf = HuggingFaceEmbeddings(model_name=model_name)

i =0

for item in ["https://arxiv.org/pdf/2302.03803.pdf","https://arxiv.org/pdf/2307.13719.pdf","https://arxiv.org/pdf/2307.14274.pdf","https://arxiv.org/pdf/2307.14309.pdf"]:

    i = i+1
    loader = OnlinePDFLoader(item)
    data = loader.load()
    doc = data[0]
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents([doc])

    doc_result = hf.embed_documents([docs[0].page_content])

    print(len(doc_result[0]))
    print(len(doc_result))
    INDEX = "test_index_archive_doc"
    #res = client.indices.create(index=INDEX, body=settings)
    #print(res)

    document = {
    'name': item,
    'id': i,
    'embedding': doc_result[0],
    'description':'a good description'
    }

    id = str(i)

    response = client.index(
        index = INDEX,
        body = document,
        id = id,
        refresh = True
    )

    print(response)

#question = "I have a question about this article"
#embeded_question = hf.embed_documents(question)
#
#query = {
#    "size": 2,
#    "query": {"knn": {"embedding": {"vector": embeded_question, "k": 2}}},
#    "_source": False,
#    "fields": ["id", "name", "description"],
#}
#response = client.search(body=query, index=INDEX)  # the same as before
#print(response["hits"]["hits"])