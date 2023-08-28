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

response = client.indices.delete(
    index = INDEX
)

print(response)