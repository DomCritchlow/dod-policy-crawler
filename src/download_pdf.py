from langchain.document_loaders import OnlinePDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
from langchain.chat_models import ChatOpenAI
from langchain.document_transformers.openai_functions import create_metadata_tagger
from langchain.embeddings import HuggingFaceEmbeddings
from elasticsearch import Elasticsearch
from langchain.vectorstores import ElasticVectorSearch

from langchain.embeddings import ElasticsearchEmbeddings


import os 

es_connection = Elasticsearch(hosts=["elasticsearch://elasticsearch:9200"], basic_auth=(os.environ['ELASTIC_USERNAME'], os.environ['ELASTIC_PASSWORD']))
print(es_connection.info())

model_name = "sentence-transformers/all-mpnet-base-v2"
hf = HuggingFaceEmbeddings(model_name=model_name)

loader = OnlinePDFLoader("https://arxiv.org/pdf/2302.03803.pdf")


schema = {
    "properties": {
        "movie_title": {"type": "string"},
        "critic": {"type": "string"},
        "tone": {"type": "string", "enum": ["positive", "negative"]},
        "rating": {
            "type": "integer",
            "description": "The number of stars the critic rated the movie",
        },
    },
    "required": ["movie_title", "critic", "tone"],
}


data = loader.load()
#print(data)

doc = data[0]
#print(type(doc))
doc.metadata = schema
print(type(doc))
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

#print(doc)

docs = text_splitter.split_documents([doc])

print(docs)

hf = HuggingFaceEmbeddings(model_name=model_name)

#embeddings = ElasticsearchEmbeddings.from_es_connection()



index_name = "test_index"

username = os.environ['ELASTIC_USERNAME']
password = os.environ['ELASTIC_PASSWORD']
url = f"elasticsearch://{username}:{password}@elasticsearch:9200"
db = ElasticVectorSearch(embedding=hf, elasticsearch_url=url, index_name=index_name)
ElasticVectorSearch()
db.add_documents(docs)

#print(docs)


# data = loader.load()


# text_splitter = RecursiveCharacterTextSplitter(
#     # Set a really small chunk size, just to show.
#     chunk_size = 100,
#     chunk_overlap  = 20,
#     length_function = len,
#     add_start_index = True,
# )

# print(data[0].page_content)

# texts = text_splitter.create_documents([data[0].page_content])





# es_connection.transport.close() """