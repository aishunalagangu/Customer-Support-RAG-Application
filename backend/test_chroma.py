
import chromadb

client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_collection("customer_support")

print("Collection metadata:", collection.metadata)
print("Collection configuration:", collection.configuration)
print("Stored vectors:", collection.count())
