
from rag.chroma_retriever import get_vector_store, COLLECTION_NAME

vectorstore = get_vector_store()

questions = [
    "What is the laptop warranty period?",
    "How can I troubleshoot mobile charging problems?",
    "What should I do if my laptop does not turn on?",
    "What should I do if my mobile phone does not turn on?",
]

print("\nProduction collection:", COLLECTION_NAME)
print("Total vectors:", vectorstore._collection.count())

for question in questions:
    print("\n" + "=" * 65)
    print("QUESTION:", question)

    results = vectorstore.similarity_search_with_score(
        question,
        k=4,
    )

    for index, (document, distance) in enumerate(results, start=1):
        print(f"\nResult {index}")
        print("Source:", document.metadata.get("source"))
        print("Page:", document.metadata.get("page"))
        print("Cosine distance:", round(distance, 4))
        print("Content:", document.page_content[:300])

print("\nProduction retrieval test completed.")
