
from pathlib import Path
import hashlib

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.embeddings import get_embeddings


# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENTS_PATH = Path("documents")
CHROMA_PATH = "chroma_db"

# A separate collection: your original collection is untouched.
COLLECTION_NAME = "customer_support_cosine_test_v1"


# ============================================================
# EMBEDDING MODEL
# ============================================================

embeddings = get_embeddings()


# ============================================================
# CREATE COSINE COLLECTION
# ============================================================

vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_PATH,
    embedding_function=embeddings,
    collection_metadata={"hnsw:space": "cosine"}
)

print("\n========== COSINE COLLECTION ==========")
print("Collection:", COLLECTION_NAME)
print("Metadata:", vectorstore._collection.metadata)
print("Configuration:", vectorstore._collection.configuration)
print("Existing test vectors:", vectorstore._collection.count())


# ============================================================
# TEXT SPLITTER
# ============================================================

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150
)


# ============================================================
# INDEX PDF DOCUMENTS
# ============================================================

pdf_files = sorted(DOCUMENTS_PATH.glob("*.pdf"))

if not pdf_files:
    raise FileNotFoundError(
        f"No PDF files found in {DOCUMENTS_PATH.resolve()}"
    )

for pdf_path in pdf_files:

    print(f"\nProcessing: {pdf_path.name}")

    # Load PDF pages.
    documents = PyPDFLoader(str(pdf_path)).load()

    if not documents:
        print("No readable pages. Skipping this PDF.")
        continue

    # Create chunks.
    for document in documents:
        document.metadata["source"] = pdf_path.name
        document.metadata["document_name"] = pdf_path.name

    chunks = text_splitter.split_documents(documents)

    if not chunks:
        print("No text chunks found. Skipping this PDF.")
        continue

    # Generate deterministic IDs for repeatable test runs.
    chunk_ids = []

    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index

        raw_id = f"{pdf_path.name}:{index}"
        chunk_id = hashlib.sha256(
            raw_id.encode("utf-8")
        ).hexdigest()

        chunk_ids.append(chunk_id)

    # Embed chunks and store them in the test collection.
    vectorstore.add_documents(
        documents=chunks,
        ids=chunk_ids
    )

    print(f"Pages loaded: {len(documents)}")
    print(f"Chunks indexed: {len(chunks)}")


# ============================================================
# VERIFY COLLECTION
# ============================================================

print("\n========== VERIFICATION ==========")
print("Metadata:", vectorstore._collection.metadata)
print("Configuration:", vectorstore._collection.configuration)
print("Total vectors:", vectorstore._collection.count())

# Confirm the actual configured metric.
configuration = vectorstore._collection.configuration
hnsw_config = configuration.get("hnsw", {})

if hnsw_config.get("space") == "cosine":
    print("SUCCESS: Cosine distance is configured.")
else:
    print("WARNING: The collection is not configured for cosine.")

print("==================================")
