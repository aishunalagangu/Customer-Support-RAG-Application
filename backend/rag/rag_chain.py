
from pathlib import Path

from rag.chroma_retriever import get_retriever
from rag.llm import generate_answer


# ============================================================
# DOCUMENTS DIRECTORY
# ============================================================

DOCUMENTS_PATH = Path("documents")


# ============================================================
# GET CURRENTLY AVAILABLE PDF FILES
# ============================================================

def get_available_pdf_names():
    """
    Return the names of PDFs that currently exist
    in the documents folder.

    This prevents deleted PDFs whose old embeddings
    still exist in ChromaDB from being retrieved.
    """

    if not DOCUMENTS_PATH.exists():
        return set()

    return {
        file.name
        for file in DOCUMENTS_PATH.iterdir()
        if file.is_file()
        and file.suffix.lower() == ".pdf"
    }


# ============================================================
# FILTER RETRIEVED DOCUMENTS
# ============================================================

def filter_current_documents(documents):
    """
    Remove documents whose source PDF no longer exists
    in the current documents folder.
    """

    available_pdfs = get_available_pdf_names()

    valid_documents = []

    for document in documents:

        source = document.metadata.get(
            "source"
        )

        if not source:
            continue

        # ----------------------------------------------------
        # Normalize source path
        # ----------------------------------------------------

        source_name = Path(
            str(source)
        ).name

        # ----------------------------------------------------
        # Keep only PDFs that currently exist
        # ----------------------------------------------------

        if source_name in available_pdfs:
            valid_documents.append(
                document
            )

    return valid_documents


# ============================================================
# ASK RAG
# ============================================================

def ask_rag(question, history=None):

    if history is None:
        history = []

    # --------------------------------------------------------
    # Get retriever
    # --------------------------------------------------------

    retriever = get_retriever()

    # --------------------------------------------------------
    # Get currently available PDFs
    # --------------------------------------------------------

    available_pdfs = get_available_pdf_names()

    print(
        "\nCurrently available PDFs:"
    )

    for pdf in sorted(
        available_pdfs
    ):
        print(
            f"  - {pdf}"
        )

    # --------------------------------------------------------
    # Build previous conversation
    # --------------------------------------------------------

    conversation = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in history[-6:]
    )

    # --------------------------------------------------------
    # Retrieve documents
    # --------------------------------------------------------

    documents = retriever.invoke(
        question
    )

    print(
        f"\nRetrieved {len(documents)} documents "
        "from ChromaDB."
    )

    # --------------------------------------------------------
    # Remove stale/deleted PDF documents
    # --------------------------------------------------------

    documents = filter_current_documents(
        documents
    )

    print(
        f"Valid documents after filtering: "
        f"{len(documents)}"
    )

    # --------------------------------------------------------
    # Show valid sources in backend console
    # --------------------------------------------------------

    if documents:

        print(
            "Valid sources:"
        )

        for document in documents:

            source = document.metadata.get(
                "source"
            )

            print(
                f"  - {source}"
            )

    else:

        print(
            "No valid PDF documents found."
        )

    # --------------------------------------------------------
    # Create context
    # --------------------------------------------------------

    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    # --------------------------------------------------------
    # Build prompt
    # --------------------------------------------------------

    enhanced_question = f"""
You are an AI customer support assistant.

Your job is to answer the customer's question using
the provided knowledge base context.

IMPORTANT RULES:

1. Use the provided context as the primary source of information.
2. Do not invent policies, warranty details, prices, procedures,
   or technical information that is not present in the context.
3. If the answer cannot be found in the context, clearly say that
   the information is not available in the current knowledge base.
4. Give a clear and professional customer-support response.
5. Use the previous conversation only when it helps understand
   the customer's current question.
6. Do not mention internal retrieval, embeddings, FAISS, or RAG
   unless the customer specifically asks about the system.

Previous Conversation:
{conversation}

Knowledge Base Context:
{context}

Current Customer Question:
{question}
"""

    # --------------------------------------------------------
    # Generate answer
    # --------------------------------------------------------

    answer = generate_answer(
        enhanced_question,
        context
    )

    # --------------------------------------------------------
    # Extract unique valid sources
    # --------------------------------------------------------

    sources = []

    for document in documents:

        source = document.metadata.get(
            "source"
        )

        if not source:
            continue

        # ----------------------------------------------------
        # Only return the filename
        # ----------------------------------------------------

        source_name = Path(
            str(source)
        ).name

        # ----------------------------------------------------
        # Double-check that the PDF exists
        # ----------------------------------------------------

        if (
            source_name in available_pdfs
            and source_name not in sources
        ):
            sources.append(
                source_name
            )

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {
        "answer": answer,
        "sources": sources
    }