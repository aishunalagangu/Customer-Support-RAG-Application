
from pathlib import Path
import hashlib

from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

from rag.embeddings import get_embeddings


# ============================================================
# CHROMA CONFIGURATION
# ============================================================

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "customer_support_cosine_v2"

DOCUMENTS_PATH = Path("documents")
DOCUMENTS_PATH.mkdir(parents=True, exist_ok=True)


# ============================================================
# EMBEDDING MODEL
# ============================================================

embeddings = get_embeddings()


# ============================================================
# CHROMA VECTOR STORE
# ============================================================

vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_PATH,
    embedding_function=embeddings,
    collection_metadata={"hnsw:space": "cosine"}
)

# Inspect the actual existing collection metadata.
print("\n========== CHROMADB CONFIGURATION ==========")
print("Collection name:", COLLECTION_NAME)
print("Collection metadata:", vectorstore._collection.metadata)
print("Stored vector count:", vectorstore._collection.count())
print("============================================\n")


# ============================================================
# RETRIEVER
# ============================================================

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}
)


# ============================================================
# TEXT SPLITTER
# ============================================================

# chunk_size and chunk_overlap are character-based here,
# because the default length function measures characters.
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150
)


# ============================================================
# GET RETRIEVER
# ============================================================

def get_retriever():
    return retriever


# ============================================================
# GET VECTOR STORE
# ============================================================

def get_vector_store():
    return vectorstore


# ============================================================
# CALCULATE PDF CONTENT HASH
# ============================================================

def calculate_file_hash(pdf_path: str) -> str:
    """Return a SHA-256 hash of the complete PDF file."""

    sha256 = hashlib.sha256()

    with open(pdf_path, "rb") as file:
        while True:
            data = file.read(1024 * 1024)

            if not data:
                break

            sha256.update(data)

    return sha256.hexdigest()


# ============================================================
# CREATE UNIQUE CHUNK ID
# ============================================================

def create_chunk_id(
    filename: str,
    file_hash: str,
    chunk_index: int
) -> str:
    """Create a deterministic ID for each PDF chunk."""

    filename_hash = hashlib.md5(
        filename.encode("utf-8")
    ).hexdigest()[:12]

    content_hash = file_hash[:16]

    return f"{filename_hash}_{content_hash}_{chunk_index}"


# ============================================================
# GET EXISTING FILE INFORMATION
# ============================================================

def get_existing_file_info(filename: str) -> dict:
    """Find existing chunks and their content hash."""

    try:
        results = vectorstore._collection.get(
            where={"source": filename},
            include=["metadatas"]
        )

        ids = results.get("ids", [])
        metadatas = results.get("metadatas", [])

        existing_hash = None

        for metadata in metadatas:
            if metadata:
                existing_hash = metadata.get("file_hash")

                if existing_hash:
                    break

        return {
            "hash": existing_hash,
            "ids": ids
        }

    except Exception as e:
        print(f"Error checking ChromaDB data: {e}")
        raise


# ============================================================
# DELETE ALL EMBEDDINGS FOR A FILENAME
# ============================================================

def delete_pdf_from_vector_store(filename: str) -> dict:
    """Delete all stored chunks belonging to one PDF filename."""

    results = vectorstore._collection.get(
        where={"source": filename},
        include=[]
    )

    ids = results.get("ids", [])

    if ids:
        vectorstore._collection.delete(ids=ids)

    print(f"Removed {len(ids)} old chunks for {filename}.")

    return {
        "filename": filename,
        "deleted_chunks": len(ids)
    }


# ============================================================
# ADD / UPDATE PDF
# ============================================================

def add_pdf_to_vector_store(
    pdf_path: str,
    original_filename: str | None = None
) -> dict:
    """
    New PDF:
        Create and store embeddings.

    Same filename and same content:
        Reuse existing embeddings.

    Same filename and changed content:
        Store new chunks, then remove the old chunks.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF file not found: {pdf_path}"
        )

    filename = pdf_path.name

    print("\n" + "=" * 50)
    print(f"Processing PDF: {filename}")

    # --------------------------------------------------------
    # 1. Calculate content hash
    # --------------------------------------------------------

    new_file_hash = calculate_file_hash(str(pdf_path))

    print(f"New content hash: {new_file_hash[:16]}...")

    # --------------------------------------------------------
    # 2. Find existing records
    # --------------------------------------------------------

    existing_info = get_existing_file_info(filename)
    old_file_hash = existing_info["hash"]
    old_ids = existing_info["ids"]

    print("DEBUG - Filename:", filename)
    print("DEBUG - Existing hash:", old_file_hash)
    print("DEBUG - Existing IDs:", old_ids)
    print("DEBUG - Existing chunk count:", len(old_ids))

    # --------------------------------------------------------
    # 3. Same filename + same content
    # --------------------------------------------------------

    if (
        old_file_hash == new_file_hash
        and old_ids
    ):
        print("Same filename and same content detected.")
        print("Reusing existing embeddings.")
        print("=" * 50)

        return {
            "filename": filename,
            "status": "unchanged",
            "pages": 0,
            "chunks": 0,
            "deleted_chunks": 0,
            "file_hash": new_file_hash,
            "message": (
                "The PDF content is unchanged. "
                "Existing embeddings were reused."
            )
        }

    # --------------------------------------------------------
    # 4. Load and split the PDF BEFORE changing stored data
    # --------------------------------------------------------

    loader = PyPDFLoader(str(pdf_path))
    documents = loader.load()

    if not documents:
        raise ValueError(
            "No readable content was found in the PDF."
        )

    for document in documents:
        document.metadata["source"] = filename
        document.metadata["document_name"] = filename
        document.metadata["file_hash"] = new_file_hash

    chunks = text_splitter.split_documents(documents)

    if not chunks:
        raise ValueError(
            "No text chunks could be created from the PDF."
        )

    print(f"PDF pages loaded: {len(documents)}")
    print(f"New chunks created: {len(chunks)}")

    # --------------------------------------------------------
    # 5. Assign chunk IDs and metadata
    # --------------------------------------------------------

    chunk_ids = []

    for index, chunk in enumerate(chunks):
        chunk.metadata["source"] = filename
        chunk.metadata["document_name"] = filename
        chunk.metadata["file_hash"] = new_file_hash
        chunk.metadata["chunk_index"] = index

        chunk_id = create_chunk_id(
            filename,
            new_file_hash,
            index
        )

        chunk.metadata["chunk_id"] = chunk_id
        chunk_ids.append(chunk_id)

    # --------------------------------------------------------
    # 6. Store new chunks and embeddings FIRST
    # --------------------------------------------------------

    print("Creating and storing new embeddings...")

    vectorstore.add_documents(
        documents=chunks,
        ids=chunk_ids
    )

    print(f"Stored {len(chunks)} new chunks.")

    # --------------------------------------------------------
    # 7. Delete only the previous chunk IDs
    # --------------------------------------------------------

    deleted_chunks = 0

    if old_ids:
        vectorstore._collection.delete(ids=old_ids)
        deleted_chunks = len(old_ids)

        print(f"Deleted {deleted_chunks} old chunks.")

    status = "updated" if old_ids else "created"

    # --------------------------------------------------------
    # 8. Return result
    # --------------------------------------------------------

    if status == "updated":
        message = (
            f"{filename} was updated. "
            f"Stored {len(chunks)} new chunks and "
            f"removed {deleted_chunks} old chunks."
        )
    else:
        message = (
            f"{filename} was added successfully with "
            f"{len(chunks)} chunks."
        )

    print(f"PDF status: {status}")
    print("=" * 50)

    return {
        "filename": filename,
        "status": status,
        "pages": len(documents),
        "chunks": len(chunks),
        "deleted_chunks": deleted_chunks,
        "file_hash": new_file_hash,
        "message": message
    }
