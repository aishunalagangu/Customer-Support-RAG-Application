
from pathlib import Path

from rag.chroma_retriever import (
    COLLECTION_NAME,
    DOCUMENTS_PATH,
    add_pdf_to_vector_store,
    get_vector_store,
)

def main():
    pdf_files = sorted(DOCUMENTS_PATH.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in the documents folder.")
        return

    print("\nPDF files to process:")
    for pdf in pdf_files:
        print(f"- {pdf.name}")

    confirmation = input(
        "\nCheck the list above. Type YES to continue indexing: "
    )

    if confirmation.strip().upper() != "YES":
        print("Indexing cancelled.")
        return

    for pdf in pdf_files:
        try:
            result = add_pdf_to_vector_store(str(pdf))

            print("\nIndexing result:")
            print(result)

        except Exception as error:
            print(f"\nFailed to process {pdf.name}: {error}")
            raise

    vectorstore = get_vector_store()
    collection = vectorstore._collection

    print("\n========== FINAL COLLECTION STATUS ==========")
    print("Collection:", COLLECTION_NAME)
    print("Metadata:", collection.metadata)
    print("Total stored vectors:", collection.count())

    for pdf in pdf_files:
        result = collection.get(
            where={"source": pdf.name},
            include=["metadatas"],
        )

        print(f"\nPDF: {pdf.name}")
        print("Stored chunks:", len(result["ids"]))

        hashes = {
            metadata.get("file_hash")
            for metadata in result["metadatas"]
            if metadata and metadata.get("file_hash")
        }
        print("Content hashes:", hashes)

    print("\nIndexing verification complete.")


if __name__ == "__main__":
    main()
