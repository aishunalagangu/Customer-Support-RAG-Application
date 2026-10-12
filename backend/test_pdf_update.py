
from pathlib import Path

from rag.chroma_retriever import (
    COLLECTION_NAME,
    DOCUMENTS_PATH,
    add_pdf_to_vector_store,
    get_vector_store,
)

PDF_PATH = DOCUMENTS_PATH / "Update_Test_Knowledge.pdf"


def main():
    if not PDF_PATH.exists():
        print(f"Test PDF not found: {PDF_PATH}")
        return

    vectorstore = get_vector_store()

    print("Collection:", COLLECTION_NAME)
    print("Vectors before processing:", vectorstore._collection.count())

    result = add_pdf_to_vector_store(str(PDF_PATH))

    print("\nIndexing result:")
    print(result)

    stored = vectorstore._collection.get(
        where={"source": PDF_PATH.name},
        include=["metadatas"],
    )

    print("\nVerification")
    print("Test PDF:", PDF_PATH.name)
    print("Stored chunks:", len(stored["ids"]))
    print(
        "Stored hashes:",
        {
            m.get("file_hash")
            for m in stored["metadatas"]
            if m and m.get("file_hash")
        },
    )

    print("\nSearch for current test content:")
    results = vectorstore.similarity_search_with_score(
        "What is the test device warranty period?",
        k=4,
        filter={"source": PDF_PATH.name},
    )

    for document, distance in results:
        print("Distance:", round(distance, 4))
        print("Content:", document.page_content[:300])


if __name__ == "__main__":
    main()
