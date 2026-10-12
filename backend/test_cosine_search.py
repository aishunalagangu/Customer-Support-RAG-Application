
from langchain_chroma import Chroma
from rag.embeddings import get_embeddings

COLLECTION_NAME = "customer_support_cosine_test_v1"

LAPTOP_PDF = "Laptop_Support_Knowledge_Base.pdf"
MOBILE_PDF = "Mobile_Support_Knowledge_Base (1).pdf"

vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory="chroma_db",
    embedding_function=get_embeddings()
)


def get_source_filter(question):
    question = question.lower()

    mobile_keywords = [
        "mobile", "phone", "smartphone",
        "android", "iphone", "cellphone"
    ]

    laptop_keywords = [
        "laptop", "notebook", "windows",
        "keyboard", "touchpad"
    ]

    if any(word in question for word in mobile_keywords):
        return {"source": MOBILE_PDF}

    if any(word in question for word in laptop_keywords):
        return {"source": LAPTOP_PDF}

    return None


questions = [
    "What is the laptop warranty period?",
    "How can I troubleshoot mobile charging problems?",
    "What should I do if my laptop does not turn on?",
]

for question in questions:
    print("\n" + "=" * 60)
    print("QUESTION:", question)

    source_filter = get_source_filter(question)

    if source_filter:
        print("Document filter:", source_filter["source"])

    results = vectorstore.similarity_search_with_score(
        question,
        k=4,
        filter=source_filter
    ) if source_filter else vectorstore.similarity_search_with_score(
        question,
        k=4
    )

    for index, (document, distance) in enumerate(results, start=1):
        print(f"\nResult {index}")
        print("Source:", document.metadata.get("source"))
        print("Page:", document.metadata.get("page"))
        print("Cosine distance:", round(distance, 4))
        print("Content:", document.page_content[:250])
