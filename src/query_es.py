from elasticsearch import Elasticsearch
import os
es_connection = Elasticsearch(hosts=["elasticsearch://elasticsearch:9200"], basic_auth=(os.environ['ELASTIC_USERNAME'], os.environ['ELASTIC_PASSWORD']))

# Get all documents in the index
documents = es_connection.search(index="test_index")

# Print the documents
for document in documents['hits']['hits']:
    print(document['_source'])


es_connection.transport.close()