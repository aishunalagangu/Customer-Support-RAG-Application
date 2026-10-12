
from rag.chroma_retriever import get_vector_store, COLLECTION_NAME

vectorstore = get_vector_store()
collection = vectorstore._collection

print("\n========== PDF VECTOR DIAGNOSTIC ==========")
print("Collection:", COLLECTION_NAME)
print("Total vectors:", collection.count())

results = collection.get(include=["metadatas"])

source_counts = {}

for metadata in results.get("metadatas", []):
    if metadata:
        source = metadata.get("source", "UNKNOWN")
        source_counts[source] = source_counts.get(source, 0) + 1

print("\nStored PDF sources:")
for source, count in sorted(source_counts.items()):
    print(f"{source}: {count} chunks")

test_name = "Update_Test_Knowledge.pdf"

test_results = collection.get(
    where={"source": test_name},
    include=["metadatas", "documents"],
)

print(f"\nChunks for {test_name}: {len(test_results['ids'])}")

for index, metadata in enumerate(test_results["metadatas"], start=1):
    print(f"\nChunk {index}")
    print("ID:", test_results["ids"][index - 1])
    print("Hash:", metadata.get("file_hash"))
    print("Content:", test_results["documents"][index - 1][:250])

print("\n===========================================")
