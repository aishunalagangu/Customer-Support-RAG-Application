import os

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.embeddings import get_embeddings


PDF_PATH = "documents/customer_support_guide.pdf"
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "customer_support"


def create_chroma_db():

    print("Loading PDF...")

    loader = PyPDFLoader(PDF_PATH)
    documents = loader.load()

    print(f"Loaded {len(documents)} PDF pages.")

    print("Splitting documents into chunks...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = text_splitter.split_documents(documents)

    print(f"Created {len(chunks)} chunks.")

    print("Loading embedding model...")

    embeddings = get_embeddings()

    print("Creating ChromaDB...")

    # Remove old ChromaDB if you want to rebuild it manually.
    # Do not delete automatically here because the database is persistent.

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
        collection_name=COLLECTION_NAME
    )

    print("ChromaDB created successfully!")
    print(f"Location: {os.path.abspath(CHROMA_PATH)}")


if __name__ == "__main__":
    create_chroma_db()