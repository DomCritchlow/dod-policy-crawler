from elasticsearch import Elasticsearch
import os 
from langchain.embeddings import HuggingFaceEmbeddings, SentenceTransformerEmbeddings
from langchain.vectorstores import ElasticVectorSearch
from langchain.document_loaders import OnlinePDFLoader
from langchain.text_splitter import CharacterTextSplitter
from opensearchpy import OpenSearch
INDEX = "test_index_archive_doc"

host = 'opensearch'
port = 9200
auth = ('admin', 'admin') # For testing only. Don't store credentials in code.

client = OpenSearch(
    hosts = [{'host': host, 'port': port}],
)
model_name = "sentence-transformers/all-mpnet-base-v2"
hf = HuggingFaceEmbeddings(model_name=model_name)


question = "I have a question about this article"
embeded_question = hf.embed_documents(question)
print(embeded_question[0])
query = {
    "query": {"knn": {"embedding": {"vector": embeded_question, "k": 2}}},
}


response = client.search(body=query, index=INDEX)  # the same as before
print(response["hits"]["hits"])