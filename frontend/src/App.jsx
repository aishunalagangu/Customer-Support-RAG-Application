import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  Send,
  Bot,
  User,
  Plus,
  Trash2,
  MessageSquare,
  LogOut,
  Copy,
  Pencil,
  Check,
  X,
  MoreVertical,
  ThumbsUp,
  ThumbsDown,
  BarChart3,
  Upload,
  FileText,
} from "lucide-react";

import Auth from "./Auth";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const welcomeMessage = {
  role: "assistant",
  content:
    "Hello! I'm your AI Customer Support Assistant. How can I help you today?",
  sources: [],
  time: "",
};

/* =======================================
   INDIA STANDARD TIME
======================================= */

function getCurrentTime() {
  return new Date().toLocaleTimeString("en-IN", {
    timeZone: "Asia/Kolkata",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}

/* =======================================
   CHECK TODAY
======================================= */

function isConversationToday(date) {
  if (!date) {
    return false;
  }

  const conversationDate = new Date(date);

  if (Number.isNaN(conversationDate.getTime())) {
    return false;
  }

  const formatter = new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });

  return (
    formatter.format(conversationDate) ===
    formatter.format(new Date())
  );
}

/* =======================================
   DATABASE TIME → IST
======================================= */

function formatDatabaseTime(dateValue) {
  if (!dateValue) {
    return "";
  }

  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleTimeString("en-IN", {
    timeZone: "Asia/Kolkata",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}

/* =======================================
   APP
======================================= */

function App() {
  /* =====================================
     STATE
  ===================================== */

  const [messages, setMessages] = useState([welcomeMessage]);

  const [searchTerm, setSearchTerm] = useState("");

  const [question, setQuestion] = useState("");

  const [loading, setLoading] = useState(false);

  const [sessionId, setSessionId] = useState(null);

  const [conversations, setConversations] = useState([]);

  const [editingConversationId, setEditingConversationId] =
    useState(null);

  const [editingTitle, setEditingTitle] = useState("");

  const [openMenuId, setOpenMenuId] = useState(null);

  const [copiedIndex, setCopiedIndex] = useState(null);

  const [feedbackStatus, setFeedbackStatus] = useState({});

  const [showDashboard, setShowDashboard] = useState(false);

  const [feedbackStats, setFeedbackStats] = useState({
    total_feedback: 0,
    positive_feedback: 0,
    negative_feedback: 0,
    positive_rate: 0,
  });

  /* =====================================
     PDF STATES
  ===================================== */

  const [uploadedPdfs, setUploadedPdfs] = useState([]);

  const [uploadingPdf, setUploadingPdf] = useState(false);

  const [deletingPdf, setDeletingPdf] = useState("");

  const [uploadMessage, setUploadMessage] = useState("");

  const [uploadError, setUploadError] = useState("");

  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem(
        "customer_support_user"
      );

      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });

  const messagesEndRef = useRef(null);

  /* =====================================
     LOAD CONVERSATIONS
  ===================================== */

  const loadConversations = async () => {
    if (!user?.id) {
      return;
    }

    try {
      console.log(
        "Loading conversations for user:",
        user.id
      );

      const response = await fetch(
        `${API_URL}/conversations?user_id=${user.id}`
      );

      console.log(
        "Conversations response status:",
        response.status
      );

      if (!response.ok) {
        const errorText = await response.text();

        console.error(
          "Conversations API error:",
          errorText
        );

        throw new Error(
          "Failed to load conversations"
        );
      }

      const data = await response.json();

      console.log(
        "Conversations response:",
        data
      );

      if (Array.isArray(data)) {
        setConversations(data);
      } else if (
        Array.isArray(data.conversations)
      ) {
        setConversations(data.conversations);
      } else {
        setConversations([]);
      }
    } catch (error) {
      console.error(
        "Conversation loading error:",
        error
      );

      setConversations([]);
    }
  };

  /* =====================================
     LOAD FEEDBACK STATISTICS
  ===================================== */

  const loadFeedbackStats = async () => {
    if (!user?.id) {
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/feedback-stats?user_id=${user.id}`
      );

      if (!response.ok) {
        throw new Error(
          "Failed to load feedback statistics"
        );
      }

      const data = await response.json();

      setFeedbackStats({
        total_feedback:
          data.total_feedback || 0,
        positive_feedback:
          data.positive_feedback || 0,
        negative_feedback:
          data.negative_feedback || 0,
        positive_rate:
          data.positive_rate || 0,
      });
    } catch (error) {
      console.error(
        "Feedback statistics error:",
        error
      );
    }
  };

  /* =====================================
     LOAD UPLOADED PDFs
  ===================================== */

  const loadUploadedPdfs = async () => {
    try {
      const response = await fetch(
        `${API_URL}/uploaded-pdfs`
      );

      if (!response.ok) {
        throw new Error(
          "Failed to load uploaded PDFs"
        );
      }

      const data = await response.json();

      setUploadedPdfs(
        Array.isArray(data.files)
          ? data.files
          : []
      );
    } catch (error) {
      console.error(
        "Uploaded PDF loading error:",
        error
      );

      setUploadedPdfs([]);
    }
  };

  /* =====================================
     LOAD USER DATA
  ===================================== */

  useEffect(() => {
    if (user?.id) {
      loadConversations();
      loadFeedbackStats();
      loadUploadedPdfs();
    }
  }, [user]);

  /* =====================================
     AUTO SCROLL
  ===================================== */

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  /* =====================================
     FILTER CONVERSATIONS
  ===================================== */

  const filteredConversations =
    conversations.filter(
      (conversation) =>
        (conversation.title || "")
          .toLowerCase()
          .includes(searchTerm.toLowerCase())
    );

  const todayConversations =
    filteredConversations.filter(
      (conversation) =>
        isConversationToday(
          conversation.created_at
        )
    );

  const earlierConversations =
    filteredConversations.filter(
      (conversation) =>
        !isConversationToday(
          conversation.created_at
        )
    );

  /* =====================================
     LOGIN
  ===================================== */

  const handleLogin = (loggedInUser) => {
    localStorage.setItem(
      "customer_support_user",
      JSON.stringify(loggedInUser)
    );

    setUser(loggedInUser);

    setMessages([welcomeMessage]);

    setSessionId(null);

    setQuestion("");

    setSearchTerm("");

    setOpenMenuId(null);

    setFeedbackStatus({});

    setFeedbackStats({
      total_feedback: 0,
      positive_feedback: 0,
      negative_feedback: 0,
      positive_rate: 0,
    });

    setUploadMessage("");

    setUploadError("");
  };

  /* =====================================
     LOGOUT
  ===================================== */

  const logout = () => {
    localStorage.removeItem(
      "customer_support_user"
    );

    setUser(null);

    setMessages([welcomeMessage]);

    setSessionId(null);

    setConversations([]);

    setUploadedPdfs([]);

    setSearchTerm("");

    setQuestion("");

    setShowDashboard(false);

    setUploadMessage("");

    setUploadError("");
  };

  /* =====================================
     NEW CHAT
  ===================================== */

  const newChat = async () => {
    if (!user?.id) {
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/conversations`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_id: user.id,
            title: "New Conversation",
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          "Failed to create conversation"
        );
      }

      const data = await response.json();

      setSessionId(data.session_id);

      setMessages([welcomeMessage]);

      setQuestion("");

      setOpenMenuId(null);

      setFeedbackStatus({});

      await loadConversations();
    } catch (error) {
      console.error(
        "New chat error:",
        error
      );
    }
  };

  /* =====================================
     UPLOAD PDF
  ===================================== */

  const uploadPdf = async (event) => {
    const file = event.target.files?.[0];

    setUploadMessage("");

    setUploadError("");

    if (!file) {
      return;
    }

    if (
      !file.name
        .toLowerCase()
        .endsWith(".pdf")
    ) {
      setUploadError(
        "Only PDF files are allowed."
      );

      event.target.value = "";

      return;
    }

    const formData = new FormData();

    formData.append("file", file);

    setUploadingPdf(true);

    setUploadMessage(
      "Uploading and processing PDF..."
    );

    try {
      const response = await fetch(
        `${API_URL}/upload-pdf`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Failed to upload PDF."
        );
      }

      setUploadMessage(
        `${data.filename} uploaded successfully. ${data.chunks} chunks indexed.`
      );

      console.log(
        "PDF upload successful:",
        data
      );

      await loadUploadedPdfs();
    } catch (error) {
      console.error(
        "PDF upload error:",
        error
      );

      setUploadMessage("");

      setUploadError(
        error.message ||
          "Failed to upload PDF."
      );
    } finally {
      setUploadingPdf(false);

      event.target.value = "";
    }
  };

  /* =====================================
     DELETE UPLOADED PDF
  ===================================== */

  const deleteUploadedPdf = async (
    filename
  ) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${filename}"?`
    );

    if (!confirmed) {
      return;
    }

    setDeletingPdf(filename);

    setUploadMessage("");

    setUploadError("");

    try {
      const response = await fetch(
        `${API_URL}/uploaded-pdfs/${encodeURIComponent(
          filename
        )}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Failed to delete PDF."
        );
      }

      /* ---------------------------------
         REMOVE PDF IMMEDIATELY FROM UI
      --------------------------------- */

      setUploadedPdfs(
        (previous) =>
          previous.filter(
            (pdf) =>
              pdf.filename !== filename
          )
      );

      /* ---------------------------------
         SHOW DELETE RESULT
      --------------------------------- */

      setUploadMessage(
        `${filename} deleted successfully. ${
          data.deleted_chunks || 0
        } embeddings removed.`
      );

      console.log(
        "PDF deleted successfully:",
        data
      );

    } catch (error) {
      console.error(
        "PDF deletion error:",
        error
      );

      setUploadError(
        error.message ||
          "Failed to delete PDF."
      );

    } finally {
      setDeletingPdf("");
    }
  };

  /* =====================================
     COPY MESSAGE
  ===================================== */

  const copyMessage = async (
    content,
    index
  ) => {
    try {
      await navigator.clipboard.writeText(
        content
      );

      setCopiedIndex(index);

      setTimeout(() => {
        setCopiedIndex(null);
      }, 1500);
    } catch (error) {
      console.error(
        "Copy failed:",
        error
      );

      try {
        const textarea =
          document.createElement(
            "textarea"
          );

        textarea.value = content;

        textarea.style.position = "fixed";

        textarea.style.opacity = "0";

        document.body.appendChild(
          textarea
        );

        textarea.focus();

        textarea.select();

        document.execCommand("copy");

        document.body.removeChild(
          textarea
        );

        setCopiedIndex(index);

        setTimeout(() => {
          setCopiedIndex(null);
        }, 1500);
      } catch (fallbackError) {
        console.error(
          "Fallback copy failed:",
          fallbackError
        );
      }
    }
  };

  /* =====================================
     SUBMIT FEEDBACK
  ===================================== */

  const submitFeedback = async (
    chatId,
    feedback
  ) => {
    if (!chatId || !user?.id) {
      console.error(
        "Missing chat ID or user"
      );

      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/feedback?chat_id=${chatId}&user_id=${user.id}&feedback=${feedback}`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        const errorText =
          await response.text();

        console.error(
          "Feedback error:",
          errorText
        );

        return;
      }

      setFeedbackStatus(
        (previous) => ({
          ...previous,
          [chatId]: feedback,
        })
      );

      await loadFeedbackStats();
    } catch (error) {
      console.error(
        "Feedback submission error:",
        error
      );
    }
  };

  /* =====================================
     OPEN CONVERSATION
  ===================================== */

  const openConversation = async (
    conversation
  ) => {
    if (!user?.id) {
      return;
    }

    setOpenMenuId(null);

    setFeedbackStatus({});

    try {
      const response = await fetch(
        `${API_URL}/chat-history/${conversation.session_id}?user_id=${user.id}`
      );

      if (!response.ok) {
        throw new Error(
          "Failed to load conversation"
        );
      }

      const data = await response.json();

      const conversationMessages = [];

      const historyMessages =
        Array.isArray(data.messages)
          ? data.messages
          : Array.isArray(data)
          ? data
          : [];

      historyMessages.forEach((item) => {
        const messageTime =
          formatDatabaseTime(
            item.created_at
          );

        conversationMessages.push({
          role: "user",
          content:
            item.user_message || "",
          sources: [],
          time: messageTime,
        });

        let sources = [];

        if (Array.isArray(item.sources)) {
          sources = item.sources;
        } else if (item.sources) {
          try {
            const parsed =
              JSON.parse(item.sources);

            sources = Array.isArray(parsed)
              ? parsed
              : [item.sources];
          } catch {
            sources = [item.sources];
          }
        }

        conversationMessages.push({
          role: "assistant",
          content:
            item.ai_response || "",
          sources,
          time: messageTime,
          chatId:
            item.chat_id ||
            item.id ||
            null,
        });
      });

      if (
        conversationMessages.length ===
        0
      ) {
        conversationMessages.push(
          welcomeMessage
        );
      }

      setMessages(
        conversationMessages
      );

      setSessionId(
        conversation.session_id
      );

      setQuestion("");
    } catch (error) {
      console.error(
        "Conversation loading error:",
        error
      );
    }
  };

  /* =====================================
     ASK QUESTION
  ===================================== */

  const askQuestion = async () => {
    if (
      !question.trim() ||
      loading ||
      !user?.id
    ) {
      return;
    }

    const userQuestion =
      question.trim();

    let currentSessionId =
      sessionId;

    if (!currentSessionId) {
      try {
        const response =
          await fetch(
            `${API_URL}/conversations`,
            {
              method: "POST",
              headers: {
                "Content-Type":
                  "application/json",
              },
              body: JSON.stringify({
                user_id: user.id,
                title:
                  userQuestion.substring(
                    0,
                    50
                  ),
              }),
            }
          );

        if (!response.ok) {
          throw new Error(
            "Failed to create conversation"
          );
        }

        const data =
          await response.json();

        currentSessionId =
          data.session_id;

        setSessionId(
          currentSessionId
        );
      } catch (error) {
        console.error(
          "Session creation error:",
          error
        );

        return;
      }
    }

    const historyForBackend =
      messages.map((message) => ({
        role: message.role,
        content: message.content,
      }));

    const userMessage = {
      role: "user",
      content: userQuestion,
      sources: [],
      time: getCurrentTime(),
    };

    setMessages((previous) => [
      ...previous,
      userMessage,
    ]);

    setQuestion("");

    setLoading(true);

    try {
      const response =
        await fetch(
          `${API_URL}/chat`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              question:
                userQuestion,
              session_id:
                currentSessionId,
              user_id: user.id,
              history:
                historyForBackend,
            }),
          }
        );

      if (!response.ok) {
        const errorText =
          await response.text();

        console.error(
          "Backend error:",
          errorText
        );

        throw new Error(
          "Server error"
        );
      }

      const data =
        await response.json();

      const assistantMessage = {
        role: "assistant",
        content:
          data.answer ||
          "Sorry, I couldn't generate an answer.",
        sources:
          data.sources || [],
        time: getCurrentTime(),
        chatId:
          data.chat_id ||
          data.id ||
          null,
      };

      setMessages((previous) => [
        ...previous,
        assistantMessage,
      ]);

      await loadConversations();
    } catch (error) {
      console.error(
        "Chat error:",
        error
      );

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content:
            "Sorry, I couldn't connect to the customer support server. Please make sure the backend is running.",
          sources: [],
          time: getCurrentTime(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  /* =====================================
     START RENAMING
  ===================================== */

  const startRenaming = (
    event,
    conversation
  ) => {
    event.stopPropagation();

    setEditingConversationId(
      conversation.session_id
    );

    setEditingTitle(
      conversation.title ||
        "Customer Support Conversation"
    );

    setOpenMenuId(null);
  };

  /* =====================================
     CANCEL RENAMING
  ===================================== */

  const cancelRenaming = (event) => {
    if (event) {
      event.stopPropagation();
    }

    setEditingConversationId(null);

    setEditingTitle("");
  };

  /* =====================================
     RENAME CONVERSATION
  ===================================== */

  const renameConversation = async (
    event,
    conversation
  ) => {
    event.stopPropagation();

    const newTitle =
      editingTitle.trim();

    if (!newTitle || !user?.id) {
      return;
    }

    try {
      const response =
        await fetch(
          `${API_URL}/conversations/${conversation.session_id}?user_id=${user.id}&title=${encodeURIComponent(
            newTitle
          )}`,
          {
            method: "PUT",
          }
        );

      if (!response.ok) {
        throw new Error(
          "Failed to rename conversation"
        );
      }

      setEditingConversationId(
        null
      );

      setEditingTitle("");

      await loadConversations();
    } catch (error) {
      console.error(
        "Rename conversation error:",
        error
      );
    }
  };

  /* =====================================
     TOGGLE MENU
  ===================================== */

  const toggleConversationMenu = (
    event,
    conversationId
  ) => {
    event.stopPropagation();

    setOpenMenuId(
      (currentId) =>
        currentId ===
        conversationId
          ? null
          : conversationId
    );
  };

  /* =====================================
     DELETE CONVERSATION
  ===================================== */

  const deleteConversation = async (
    event,
    conversation
  ) => {
    event.stopPropagation();

    setOpenMenuId(null);

    const confirmDelete =
      window.confirm(
        "Are you sure you want to delete this conversation?"
      );

    if (
      !confirmDelete ||
      !user?.id
    ) {
      return;
    }

    try {
      const response =
        await fetch(
          `${API_URL}/conversations/${conversation.session_id}?user_id=${user.id}`,
          {
            method: "DELETE",
          }
        );

      if (!response.ok) {
        throw new Error(
          "Failed to delete conversation"
        );
      }

      if (
        sessionId ===
        conversation.session_id
      ) {
        setSessionId(null);

        setMessages([
          welcomeMessage,
        ]);

        setQuestion("");

        setFeedbackStatus({});
      }

      await loadConversations();
    } catch (error) {
      console.error(
        "Delete conversation error:",
        error
      );
    }
  };

  /* =====================================
     CLEAR CHAT
  ===================================== */

  const clearChat = () => {
    setMessages([welcomeMessage]);

    setQuestion("");

    setSessionId(null);

    setOpenMenuId(null);

    setFeedbackStatus({});
  };

  /* =====================================
     ENTER KEY
  ===================================== */

  const handleKeyDown = (event) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      askQuestion();
    }
  };

  /* =====================================
     LOGIN SCREEN
  ===================================== */

  if (!user) {
    return (
      <Auth
        onLogin={handleLogin}
      />
    );
  }

  /* =====================================
     MAIN APPLICATION
  ===================================== */

  return (
    <div className="app">

      {/* SIDEBAR */}

      <aside className="sidebar">

        {/* BRAND */}

        <div className="brand">

          <div className="brand-icon">
            <Bot size={22} />
          </div>

          <div>
            <h2>
              Customer Support AI
            </h2>

            <span>
              AI-powered support
            </span>
          </div>

        </div>

        {/* DASHBOARD */}

        <button
          className="dashboard-btn"
          onClick={() =>
            setShowDashboard(true)
          }
        >
          <BarChart3 size={16} />
          Dashboard
        </button>

        {/* NEW CHAT */}

        <button
          className="new-chat-btn"
          onClick={newChat}
        >
          <Plus size={17} />
          New Chat
        </button>

        {/* =================================
            UPLOAD PDF
        ================================= */}

        <label
          className={`upload-pdf-btn ${
            uploadingPdf
              ? "uploading"
              : ""
          }`}
        >
          <Upload size={17} />

          <span>
            {uploadingPdf
              ? "Processing PDF..."
              : "Upload PDF"}
          </span>

          <input
            type="file"
            accept=".pdf,application/pdf"
            onChange={uploadPdf}
            disabled={uploadingPdf}
            hidden
          />
        </label>

        {/* =================================
            UPLOAD STATUS
        ================================= */}

        {uploadMessage && (
          <div className="upload-success-message">
            {uploadMessage}
          </div>
        )}

        {uploadError && (
          <div className="upload-error-message">
            {uploadError}
          </div>
        )}

        {/* =================================
            UPLOADED PDF LIST
        ================================= */}

        <div className="uploaded-pdfs-section">

          <div className="uploaded-pdfs-title">

            <span>
              Uploaded Documents
            </span>

            <span className="pdf-count">
              {uploadedPdfs.length}
            </span>

          </div>

          {uploadedPdfs.length === 0 ? (

            <div className="no-pdfs">
              No PDFs uploaded yet
            </div>

          ) : (

            <div className="uploaded-pdfs-list">

              {uploadedPdfs.map(
                (pdf) => (

                  <div
                    className="uploaded-pdf-item"
                    key={pdf.filename}
                  >

                    <div className="pdf-info">

                      <div className="pdf-icon">
                        <FileText
                          size={15}
                        />
                      </div>

                      <div className="pdf-details">

                        <span
                          className="pdf-name"
                          title={
                            pdf.filename
                          }
                        >
                          {pdf.filename}
                        </span>

                        <span className="pdf-size">

                          {(
                            pdf.size /
                            1024
                          ).toFixed(1)}{" "}
                          KB

                        </span>

                      </div>

                    </div>

                    <button
                      className="pdf-delete-btn"
                      onClick={() =>
                        deleteUploadedPdf(
                          pdf.filename
                        )
                      }
                      disabled={
                        deletingPdf ===
                        pdf.filename
                      }
                      title="Delete PDF"
                    >

                      {deletingPdf ===
                      pdf.filename ? (
                        <span className="delete-loading">
                          ...
                        </span>
                      ) : (
                        <Trash2
                          size={14}
                        />
                      )}

                    </button>

                  </div>

                )
              )}

            </div>

          )}

        </div>

        {/* CONVERSATIONS */}

        <div className="sidebar-section">

          <div className="section-title">
            <MessageSquare size={13} />
            Recent Conversations
          </div>

          <div className="conversation-search">

            <input
              type="text"
              placeholder="Search conversations..."
              value={searchTerm}
              onChange={(event) =>
                setSearchTerm(
                  event.target.value
                )
              }
            />

          </div>

        </div>

        {/* CONVERSATION HISTORY */}

        <div className="conversation-history">

          {/* TODAY */}

          {todayConversations.length >
            0 && (
            <>

              <div className="history-group-title">
                Today
              </div>

              {todayConversations.map(
                (conversation) => (
                  <ConversationItem
                    key={
                      conversation.session_id
                    }
                    conversation={
                      conversation
                    }
                    sessionId={sessionId}
                    editingConversationId={
                      editingConversationId
                    }
                    editingTitle={
                      editingTitle
                    }
                    setEditingTitle={
                      setEditingTitle
                    }
                    openMenuId={
                      openMenuId
                    }
                    openConversation={
                      openConversation
                    }
                    startRenaming={
                      startRenaming
                    }
                    renameConversation={
                      renameConversation
                    }
                    cancelRenaming={
                      cancelRenaming
                    }
                    toggleConversationMenu={
                      toggleConversationMenu
                    }
                    deleteConversation={
                      deleteConversation
                    }
                  />
                )
              )}

            </>
          )}

          {/* EARLIER */}

          {earlierConversations.length >
            0 && (
            <>

              <div className="history-group-title">
                Earlier
              </div>

              {earlierConversations.map(
                (conversation) => (
                  <ConversationItem
                    key={
                      conversation.session_id
                    }
                    conversation={
                      conversation
                    }
                    sessionId={sessionId}
                    editingConversationId={
                      editingConversationId
                    }
                    editingTitle={
                      editingTitle
                    }
                    setEditingTitle={
                      setEditingTitle
                    }
                    openMenuId={
                      openMenuId
                    }
                    openConversation={
                      openConversation
                    }
                    startRenaming={
                      startRenaming
                    }
                    renameConversation={
                      renameConversation
                    }
                    cancelRenaming={
                      cancelRenaming
                    }
                    toggleConversationMenu={
                      toggleConversationMenu
                    }
                    deleteConversation={
                      deleteConversation
                    }
                  />
                )
              )}

            </>
          )}

          {/* EMPTY HISTORY */}

          {filteredConversations.length ===
            0 && (
            <div className="empty-history">
              {searchTerm
                ? "No conversations found"
                : "No conversations yet"}
            </div>
          )}

        </div>

        {/* =================================
            FIXED BOTTOM SECTION
            Clear Chat + User Information
        ================================= */}

        <div className="sidebar-fixed-bottom">

          {/* CLEAR CHAT */}

          <button
            className="clear-btn"
            onClick={clearChat}
          >
            <Trash2 size={15} />
            Clear Chat
          </button>

          {/* USER INFORMATION */}

          <div className="sidebar-user-row">

            <div className="user-profile">

              <div className="user-profile-avatar">
                {user?.name
                  ?.charAt(0)
                  ?.toUpperCase() ||
                  "U"}
              </div>

              <div className="user-profile-info">

                <strong>
                  {user?.name || "User"}
                </strong>

                <span>
                  {user?.email || ""}
                </span>

              </div>

              {/* LOGOUT */}

              <button
                className="logout-btn"
                onClick={logout}
                title="Logout"
              >
                <LogOut size={17} />
              </button>

            </div>

          </div>

        </div>

      </aside>

      {/* CHAT AREA */}

      <main className="chat-area">

        {/* HEADER */}

        <header className="chat-header">

          <div>

            <h1>
              AI Customer Support
            </h1>

            <p>
              Ask questions about your service
            </p>

          </div>

          <div className="status">

            <span className="status-dot"></span>

            AI Online

          </div>

        </header>

        {/* MESSAGES */}

        <div className="messages">

          {messages.length === 1 &&
          messages[0].role ===
            "assistant" ? (

            <div className="welcome-screen">

              <div className="welcome-icon">
                <Bot size={38} />
              </div>

              <h2>
                How can I help you today?
              </h2>

              <p>
                Get instant answers to
                your support
                questions using our
                AI-powered customer
                support assistant.
              </p>

            </div>

          ) : (

            messages.map(
              (message, index) => (

                <div
                  key={index}
                  className={`message-row ${message.role}`}
                >

                  <div className="avatar">

                    {message.role ===
                    "assistant" ? (
                      <Bot size={19} />
                    ) : (
                      <User size={19} />
                    )}

                  </div>

                  <div className="message-content">

                    <div className="message-name">

                      {message.role ===
                      "assistant"
                        ? "AI Support"
                        : "You"}

                    </div>

                    <div className="message-bubble">

                      {message.role ===
                      "assistant" ? (

                        <ReactMarkdown
                          remarkPlugins={[
                            remarkGfm,
                          ]}
                        >
                          {message.content}
                        </ReactMarkdown>

                      ) : (

                        <div>
                          {message.content}
                        </div>

                      )}

                    </div>

                    {/* SOURCES */}

                    {message.role ===
                      "assistant" &&
                      message.sources &&
                      message.sources.length >
                        0 && (

                        <div className="sources-section">

                          <div className="sources-title">
                            📚 Sources
                          </div>

                          <div className="sources-list">

                            {message.sources.map(
                              (
                                source,
                                sourceIndex
                              ) => (

                                <div
                                  className="source-item"
                                  key={
                                    sourceIndex
                                  }
                                >

                                  <span className="source-number">
                                    {
                                      sourceIndex +
                                      1
                                    }
                                  </span>

                                  <span>

                                    {typeof source ===
                                    "string"
                                      ? source
                                      : source?.source ||
                                        source?.file ||
                                        source?.filename ||
                                        "Customer Support Guide"}

                                  </span>

                                </div>

                              )
                            )}

                          </div>

                        </div>

                      )}

                    {/* MESSAGE META */}

                    <div className="message-meta">

                      <span className="message-time">
                        {message.time}
                      </span>

                      {message.role ===
                        "assistant" && (

                        <div className="message-actions">

                          {/* COPY */}

                          <button
                            className="copy-btn"
                            onClick={() =>
                              copyMessage(
                                message.content,
                                index
                              )
                            }
                            title="Copy response"
                          >

                            {copiedIndex ===
                            index ? (
                              <>
                                <Check
                                  size={14}
                                />

                                <span>
                                  Copied!
                                </span>
                              </>
                            ) : (
                              <>
                                <Copy
                                  size={14}
                                />

                                <span>
                                  Copy
                                </span>
                              </>
                            )}

                          </button>

                          {/* LIKE */}

                          {message.chatId && (
                            <button
                              className={`feedback-btn ${
                                feedbackStatus[
                                  message.chatId
                                ] ===
                                "positive"
                                  ? "active positive"
                                  : ""
                              }`}
                              onClick={() =>
                                submitFeedback(
                                  message.chatId,
                                  "positive"
                                )
                              }
                              title="Helpful"
                            >
                              <ThumbsUp
                                size={14}
                              />
                            </button>
                          )}

                          {/* DISLIKE */}

                          {message.chatId && (
                            <button
                              className={`feedback-btn ${
                                feedbackStatus[
                                  message.chatId
                                ] ===
                                "negative"
                                  ? "active negative"
                                  : ""
                              }`}
                              onClick={() =>
                                submitFeedback(
                                  message.chatId,
                                  "negative"
                                )
                              }
                              title="Not helpful"
                            >
                              <ThumbsDown
                                size={14}
                              />
                            </button>
                          )}

                        </div>

                      )}

                    </div>

                  </div>

                </div>

              )
            )

          )}

          {/* LOADING */}

          {loading && (

            <div className="message-row assistant">

              <div className="avatar">
                <Bot size={19} />
              </div>

              <div className="message-content">

                <div className="message-name">
                  AI Support
                </div>

                <div className="message-bubble typing">

                  <span></span>
                  <span></span>
                  <span></span>

                </div>

              </div>

            </div>

          )}

          <div ref={messagesEndRef} />

        </div>

        {/* INPUT */}

        <div className="input-area">

          <div className="input-box">

            <textarea
              value={question}
              onChange={(event) =>
                setQuestion(
                  event.target.value
                )
              }
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your laptop..."
              rows="1"
            />

            <button
              className="send-btn"
              onClick={askQuestion}
              disabled={
                loading ||
                !question.trim()
              }
            >
              <Send size={19} />
            </button>

          </div>

          <div className="input-hint">
            Press Enter to send • Shift +
            Enter for a new line
          </div>

        </div>

      </main>

      {/* DASHBOARD */}

      {showDashboard && (

        <div
          className="dashboard-overlay"
          onClick={() =>
            setShowDashboard(false)
          }
        >

          <div
            className="dashboard-card"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <div className="dashboard-header">

              <div>

                <h2>
                  Feedback Dashboard
                </h2>

                <p>
                  Customer support feedback overview
                </p>

              </div>

              <button
                className="dashboard-close"
                onClick={() =>
                  setShowDashboard(false)
                }
                title="Close dashboard"
              >
                <X size={20} />
              </button>

            </div>

            <div className="stats-grid">

              <div className="stat-card">

                <div className="stat-icon">
                  <MessageSquare
                    size={20}
                  />
                </div>

                <div>

                  <span>
                    Total Feedback
                  </span>

                  <strong>
                    {feedbackStats.total_feedback}
                  </strong>

                </div>

              </div>

              <div className="stat-card">

                <div className="stat-icon">
                  <ThumbsUp
                    size={20}
                  />
                </div>

                <div>

                  <span>
                    Positive
                  </span>

                  <strong>
                    {feedbackStats.positive_feedback}
                  </strong>

                </div>

              </div>

              <div className="stat-card">

                <div className="stat-icon">
                  <ThumbsDown
                    size={20}
                  />
                </div>

                <div>

                  <span>
                    Negative
                  </span>

                  <strong>
                    {feedbackStats.negative_feedback}
                  </strong>

                </div>

              </div>

            </div>

            <div className="feedback-summary">

              <div className="progress-label">

                <span>
                  Positive Feedback Rate
                </span>

                <strong>
                  {Number(
                    feedbackStats.positive_rate
                  ).toFixed(1)}
                  %
                </strong>

              </div>

              <div className="progress-container">

                <div
                  className="progress-bar"
                  style={{
                    width: `${Math.min(
                      100,
                      Math.max(
                        0,
                        Number(
                          feedbackStats.positive_rate
                        ) || 0
                      )
                    )}%`,
                  }}
                />

              </div>

            </div>

          </div>

        </div>

      )}

    </div>
  );
}

/* =======================================
   CONVERSATION ITEM
======================================= */

function ConversationItem({
  conversation,
  sessionId,
  editingConversationId,
  editingTitle,
  setEditingTitle,
  openMenuId,
  openConversation,
  startRenaming,
  renameConversation,
  cancelRenaming,
  toggleConversationMenu,
  deleteConversation,
}) {
  return (
    <div
      className={`history-item ${
        sessionId ===
        conversation.session_id
          ? "active"
          : ""
      }`}
      onClick={() =>
        openConversation(conversation)
      }
    >

      {editingConversationId ===
      conversation.session_id ? (

        <>

          <input
            className="history-edit-input"
            value={editingTitle}
            onChange={(event) =>
              setEditingTitle(
                event.target.value
              )
            }
            onClick={(event) =>
              event.stopPropagation()
            }
            onKeyDown={(event) => {

              if (
                event.key ===
                "Escape"
              ) {
                cancelRenaming(event);
              }

              if (
                event.key ===
                "Enter"
              ) {
                renameConversation(
                  event,
                  conversation
                );
              }

            }}
            autoFocus
          />

          <div className="history-edit-actions">

            <button
              className="history-action save"
              onClick={(event) =>
                renameConversation(
                  event,
                  conversation
                )
              }
              title="Save"
            >
              <Check size={15} />
            </button>

            <button
              className="history-action cancel"
              onClick={(event) =>
                cancelRenaming(event)
              }
              title="Cancel"
            >
              <X size={15} />
            </button>

          </div>

        </>

      ) : (

        <>

          <div className="history-text">

            <span className="history-title">
              {conversation.title ||
                "Customer Support Conversation"}
            </span>

          </div>

          <div className="history-actions">

            <button
              className="history-menu-btn"
              onClick={(event) =>
                toggleConversationMenu(
                  event,
                  conversation.session_id
                )
              }
              title="More options"
            >
              <MoreVertical size={16} />
            </button>

            {openMenuId ===
              conversation.session_id && (

              <div className="conversation-menu">

                <button
                  onClick={(event) =>
                    startRenaming(
                      event,
                      conversation
                    )
                  }
                >
                  <Pencil size={14} />
                  Rename
                </button>

                <button
                  className="delete-option"
                  onClick={(event) =>
                    deleteConversation(
                      event,
                      conversation
                    )
                  }
                >
                  <Trash2 size={14} />
                  Delete
                </button>

              </div>

            )}

          </div>

        </>

      )}

    </div>
  );
}

export default App;