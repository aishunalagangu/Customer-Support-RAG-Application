from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from database import SessionLocal, engine
from models import Base, ChatHistory, User, Feedback
from schemas import ChatRequest, RegisterRequest, LoginRequest

from rag.chroma_retriever import (
    get_retriever,
    add_pdf_to_vector_store,
    delete_pdf_from_vector_store,
)

from rag.rag_chain import ask_rag

import time
import uuid
import bcrypt
import json
import os
import shutil


# ============================================================
# UPLOAD DIRECTORY
# ============================================================

UPLOAD_DIR = "documents"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AI Customer Support RAG Assistant",
    description="Customer support application using Retrieval-Augmented Generation",
    version="1.0.0"
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# RETRIEVER
# ============================================================

retriever = get_retriever()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": "AI Customer Support RAG Assistant API is running"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "Customer Support RAG API"
    }


# ============================================================
# CREATE NEW CONVERSATION
# ============================================================

@app.post("/conversations")
def create_conversation():

    session_id = str(
        uuid.uuid4()
    )

    return {
        "session_id": session_id,
        "message": "New conversation created"
    }


# ============================================================
# GET ALL CONVERSATIONS
# ============================================================

@app.get("/conversations")
def get_conversations(
    user_id: int
):

    db = SessionLocal()

    try:

        sessions = (
            db.query(
                ChatHistory.session_id
            )
            .filter(
                ChatHistory.user_id == user_id
            )
            .distinct()
            .all()
        )

        conversations = []

        for row in sessions:

            session_id = row[0]

            first_message = (
                db.query(ChatHistory)
                .filter(
                    ChatHistory.session_id == session_id,
                    ChatHistory.user_id == user_id
                )
                .order_by(
                    ChatHistory.created_at.asc()
                )
                .first()
            )

            title = (
                first_message.title
                if first_message
                and first_message.title
                else (
                    first_message.user_message[:40]
                    if first_message
                    else "New Conversation"
                )
            )

            conversations.append({
                "session_id": session_id,
                "title": title,
                "created_at": (
                    first_message.created_at
                    if first_message
                    else None
                )
            })

        return {
            "conversations": conversations
        }

    finally:

        db.close()


# ============================================================
# REGISTER
# ============================================================

@app.post("/register")
def register(
    request: RegisterRequest
):

    db = SessionLocal()

    try:

        existing_user = (
            db.query(User)
            .filter(
                User.email == request.email
            )
            .first()
        )

        if existing_user:

            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        hashed_password = bcrypt.hashpw(
            request.password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        new_user = User(
            name=request.name,
            email=request.email,
            password=hashed_password
        )

        db.add(new_user)

        db.commit()

        db.refresh(new_user)

        return {
            "message": "Registration successful",
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email
            }
        }

    finally:

        db.close()


# ============================================================
# LOGIN
# ============================================================

@app.post("/login")
def login(
    request: LoginRequest
):

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(
                User.email == request.email
            )
            .first()
        )

        if not user:

            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        if not bcrypt.checkpw(
            request.password.encode("utf-8"),
            user.password.encode("utf-8")
        ):

            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        return {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }

    finally:

        db.close()


# ============================================================
# CHAT
# ============================================================

@app.post("/chat")
def chat(
    request: ChatRequest
):

    start = time.time()

    print(
        "\n=============================="
    )

    print(
        "CHAT REQUEST RECEIVED"
    )

    print(
        "=============================="
    )

    history = [
        {
            "role": message.role,
            "content": message.content
        }
        for message in request.history
    ]

    print(
        "Session ID:",
        request.session_id
    )

    print(
        "User ID:",
        request.user_id
    )

    print(
        "Starting RAG..."
    )

    rag_start = time.time()

    result = ask_rag(
        request.question,
        history
    )

    print(
        f"RAG completed in "
        f"{time.time() - rag_start:.2f} seconds"
    )

    print(
        "Saving conversation to MySQL..."
    )

    db_start = time.time()

    db = SessionLocal()

    try:

        chat_record = ChatHistory(
            session_id=request.session_id,
            user_id=request.user_id,
            title=request.question[:40],
            user_message=request.question,
            ai_response=result["answer"],
            sources=json.dumps(
                result.get(
                    "sources",
                    []
                )
            )
        )

        db.add(chat_record)

        db.commit()

        db.refresh(chat_record)

    finally:

        db.close()

    print(
        f"MySQL completed in "
        f"{time.time() - db_start:.2f} seconds"
    )

    print(
        f"TOTAL REQUEST TIME: "
        f"{time.time() - start:.2f} seconds"
    )

    print(
        "==============================\n"
    )

    return {
        **result,
        "chat_id": chat_record.id
    }


# ============================================================
# SUBMIT FEEDBACK
# ============================================================

@app.post("/feedback")
def submit_feedback(
    chat_id: int,
    user_id: int,
    feedback: str
):

    db = SessionLocal()

    try:

        if feedback not in [
            "positive",
            "negative"
        ]:

            raise HTTPException(
                status_code=400,
                detail="Feedback must be positive or negative"
            )

        chat = (
            db.query(ChatHistory)
            .filter(
                ChatHistory.id == chat_id,
                ChatHistory.user_id == user_id
            )
            .first()
        )

        if not chat:

            raise HTTPException(
                status_code=404,
                detail="Chat message not found"
            )

        existing_feedback = (
            db.query(Feedback)
            .filter(
                Feedback.chat_id == chat_id,
                Feedback.user_id == user_id
            )
            .first()
        )

        if existing_feedback:

            existing_feedback.feedback = feedback

        else:

            new_feedback = Feedback(
                chat_id=chat_id,
                user_id=user_id,
                feedback=feedback
            )

            db.add(new_feedback)

        db.commit()

        return {
            "message": "Feedback submitted successfully",
            "chat_id": chat_id,
            "feedback": feedback
        }

    finally:

        db.close()


# ============================================================
# GET ALL CHAT HISTORY
# ============================================================

@app.get("/chat-history")
def get_chat_history(
    user_id: int
):

    db = SessionLocal()

    try:

        history = (
            db.query(ChatHistory)
            .filter(
                ChatHistory.user_id == user_id
            )
            .order_by(
                ChatHistory.created_at.asc()
            )
            .all()
        )

        return [
            {
                "chat_id": chat.id,
                "session_id": chat.session_id,
                "user_id": chat.user_id,
                "user_message": chat.user_message,
                "ai_response": chat.ai_response,
                "sources": (
                    json.loads(chat.sources)
                    if chat.sources
                    else []
                ),
                "created_at": chat.created_at,
            }
            for chat in history
        ]

    finally:

        db.close()


# ============================================================
# GET ONE CONVERSATION
# ============================================================

@app.get(
    "/chat-history/{session_id}"
)
def get_conversation(
    session_id: str,
    user_id: int
):

    db = SessionLocal()

    try:

        history = (
            db.query(ChatHistory)
            .filter(
                ChatHistory.session_id == session_id,
                ChatHistory.user_id == user_id
            )
            .order_by(
                ChatHistory.created_at.asc()
            )
            .all()
        )

        return {
            "session_id": session_id,
            "messages": [
                {
                    "chat_id": chat.id,
                    "user_message": chat.user_message,
                    "ai_response": chat.ai_response,
                    "sources": (
                        json.loads(chat.sources)
                        if chat.sources
                        else []
                    ),
                    "created_at": chat.created_at
                }
                for chat in history
            ]
        }

    finally:

        db.close()


# ============================================================
# DELETE CONVERSATION
# ============================================================

@app.delete(
    "/conversations/{session_id}"
)
def delete_conversation(
    session_id: str,
    user_id: int
):

    db = SessionLocal()

    try:

        deleted_count = (
            db.query(ChatHistory)
            .filter(
                ChatHistory.session_id == session_id,
                ChatHistory.user_id == user_id
            )
            .delete(
                synchronize_session=False
            )
        )

        db.commit()

        if deleted_count == 0:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

        return {
            "message": "Conversation deleted successfully"
        }

    finally:

        db.close()


# ============================================================
# RENAME CONVERSATION
# ============================================================

@app.put(
    "/conversations/{session_id}"
)
def rename_conversation(
    session_id: str,
    user_id: int,
    title: str
):

    db = SessionLocal()

    try:

        conversation = (
            db.query(ChatHistory)
            .filter(
                ChatHistory.session_id == session_id,
                ChatHistory.user_id == user_id
            )
            .order_by(
                ChatHistory.created_at.asc()
            )
            .first()
        )

        if not conversation:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

        cleaned_title = title.strip()

        if not cleaned_title:

            raise HTTPException(
                status_code=400,
                detail="Conversation title cannot be empty"
            )

        if len(cleaned_title) > 150:

            raise HTTPException(
                status_code=400,
                detail="Conversation title cannot exceed 150 characters"
            )

        (
            db.query(ChatHistory)
            .filter(
                ChatHistory.session_id == session_id,
                ChatHistory.user_id == user_id
            )
            .update(
                {
                    ChatHistory.title: cleaned_title
                },
                synchronize_session=False
            )
        )

        db.commit()

        return {
            "message": "Conversation renamed successfully",
            "session_id": session_id,
            "title": cleaned_title
        }

    finally:

        db.close()


# ============================================================
# FEEDBACK STATISTICS
# ============================================================

@app.get(
    "/feedback-stats"
)
def get_feedback_stats(
    user_id: int
):

    db = SessionLocal()

    try:

        total_feedback = (
            db.query(Feedback)
            .filter(
                Feedback.user_id == user_id
            )
            .count()
        )

        positive_feedback = (
            db.query(Feedback)
            .filter(
                Feedback.user_id == user_id,
                Feedback.feedback == "positive"
            )
            .count()
        )

        negative_feedback = (
            db.query(Feedback)
            .filter(
                Feedback.user_id == user_id,
                Feedback.feedback == "negative"
            )
            .count()
        )

        positive_rate = (
            round(
                (
                    positive_feedback
                    / total_feedback
                ) * 100,
                1
            )
            if total_feedback > 0
            else 0
        )

        return {
            "total_feedback": total_feedback,
            "positive_feedback": positive_feedback,
            "negative_feedback": negative_feedback,
            "positive_rate": positive_rate
        }

    finally:

        db.close()


# ============================================================
# UPLOAD PDF
# ============================================================

# ============================================================
# UPLOAD PDF - SAFER VERSION
# ============================================================

@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...)
):
    temp_path = None
    vector_update_completed = False
    result = None

    # Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid PDF file."
        )

    # Validate extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    # Prevent directory traversal
    filename = os.path.basename(file.filename)

    if filename in ("", ".", ".."):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF filename."
        )

    file_path = os.path.join(UPLOAD_DIR, filename)
    had_existing_file = os.path.isfile(file_path)

    # Save to a unique temporary PDF, not the existing file
    temp_path = os.path.join(
        UPLOAD_DIR,
        f".upload-{uuid.uuid4().hex}.pdf"
    )

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Check that the uploaded file has PDF content
        with open(temp_path, "rb") as uploaded:
            header = uploaded.read(1024)

        if b"%PDF-" not in header:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is not a valid PDF."
            )

        print(f"\nPDF upload received: {filename}")
        print("Validating and indexing temporary PDF...")

        # Validate, split, embed and update ChromaDB.
        # original_filename keeps metadata linked to the real filename.
        result = add_pdf_to_vector_store(
            temp_path,
            original_filename=filename
        )

        vector_update_completed = True

        # Replace the original file only after indexing succeeds.
        # os.replace is an atomic replacement on the same filesystem.
        try:
            os.replace(temp_path, file_path)
            temp_path = None

        except Exception:
            # Try to restore the previous vector content if the
            # disk replacement fails after indexing has completed.
            try:
                if had_existing_file and os.path.isfile(file_path):
                    add_pdf_to_vector_store(
                        file_path,
                        original_filename=filename
                    )
                else:
                    delete_pdf_from_vector_store(filename)
            except Exception as rollback_error:
                print(
                    "WARNING: Vector rollback failed:",
                    str(rollback_error)
                )

            raise

        print(f"PDF processed successfully: {filename}")
        print("Status:", result["status"])
        print("Pages:", result["pages"])
        print("Chunks:", result["chunks"])
        print("Deleted old chunks:", result["deleted_chunks"])

        if result["status"] == "unchanged":
            message = (
                "PDF content is unchanged. "
                "Existing embeddings were reused."
            )
        elif result["status"] == "updated":
            message = (
                "PDF updated successfully. "
                "New embeddings were stored and old chunks removed."
            )
        else:
            message = (
                "PDF uploaded and embedded successfully."
            )

        return {
            "message": message,
            "filename": result["filename"],
            "status": result["status"],
            "pages": result["pages"],
            "chunks": result["chunks"],
            "deleted_chunks": result["deleted_chunks"],
            "file_hash": result["file_hash"],
            "vector_database": "ChromaDB",
            "embedding_model": "nomic-embed-text"
        }

    except HTTPException:
        raise

    except Exception as e:
        print("PDF processing error:", str(e))

        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF: {str(e)}"
        )

    finally:
        # Remove only the temporary upload.
        # Never blindly delete the existing PDF on failure.
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError as cleanup_error:
                print(
                    "Temporary file cleanup warning:",
                    str(cleanup_error)
                )

        await file.close()

# ============================================================
# GET ALL UPLOADED PDFs
# ============================================================

@app.get("/uploaded-pdfs")
async def get_uploaded_pdfs():

    try:

        files = []

        for filename in os.listdir(
            UPLOAD_DIR
        ):

            if (
                    filename.lower().endswith(".pdf")
                    and not filename.startswith(".upload-")
                ):

                file_path = os.path.join(
                    UPLOAD_DIR,
                    filename
                )

                file_size = os.path.getsize(
                    file_path
                )

                files.append({
                    "filename": filename,
                    "size": file_size
                })

        files.sort(
            key=lambda item:
            item["filename"].lower()
        )

        return {
            "files": files
        }

    except Exception as e:

        print(
            "Error loading uploaded PDFs:",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to load uploaded PDFs."
        )


# ============================================================
# DELETE PDF + CHROMADB EMBEDDINGS
# ============================================================

@app.delete(
    "/uploaded-pdfs/{filename}"
)
async def delete_uploaded_pdf(
    filename: str
):

    try:

        # ----------------------------------------------------
        # MAKE FILENAME SAFE
        # ----------------------------------------------------

        safe_filename = os.path.basename(
            filename
        )

        # ----------------------------------------------------
        # VALIDATE PDF
        # ----------------------------------------------------

        if not safe_filename.lower().endswith(
            ".pdf"
        ):

            raise HTTPException(
                status_code=400,
                detail="Only PDF files can be deleted."
            )

        file_path = os.path.join(
            UPLOAD_DIR,
            safe_filename
        )

        # ----------------------------------------------------
        # CHECK PDF EXISTS
        # ----------------------------------------------------
        if not os.path.exists(
            file_path
        ):
            raise HTTPException(
                status_code=404,
                detail="PDF file not found."
            )
        print(
            "\n=============================="
        )
        print(
            "PDF DELETE REQUEST"
        )
        print(
            "=============================="
        )
        print(
            "Filename:",
            safe_filename
        )

        # ----------------------------------------------------
        # STEP 1:
        # DELETE EMBEDDINGS FROM CHROMADB
        # ----------------------------------------------------w
        print(
            "Deleting ChromaDB embeddings..."
        )

        result = delete_pdf_from_vector_store(
            safe_filename
        )

        print(
            "Deleted ChromaDB chunks:",
            result["deleted_chunks"]
        )

        # ----------------------------------------------------
        # STEP 2:
        # DELETE ORIGINAL PDF
        # ----------------------------------------------------
        print(
            "Deleting PDF file..."
        )

        os.remove(
            file_path
        )

        print(
            "PDF deleted:",
            safe_filename
        )

        print(
            "==============================\n"
        )

        return {
            "message": (
                "PDF and its ChromaDB "
                "embeddings deleted successfully."
            ),
            "filename": safe_filename,
            "deleted_chunks": result[
                "deleted_chunks"
            ]
        }

    except HTTPException:

        raise

    except Exception as e:

        print(
            "PDF deletion error:",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to delete PDF: {str(e)}"
            )
        )