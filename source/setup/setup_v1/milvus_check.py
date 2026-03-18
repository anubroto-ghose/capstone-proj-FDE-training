from pymilvus import MilvusClient

client = MilvusClient("http://localhost:19530")

# List collections
collections = client.list_collections()
print("Collections:", collections)