import { useRef, useState, useEffect } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/api/infer";

const makeChat = () => ({
  id: Date.now() + Math.random(),
  title: "New chat",
  messages: [],
});

function App() {
  const [chats, setChats] = useState([makeChat()]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [input, setInput] = useState("");
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [attachmentMenuOpen, setAttachmentMenuOpen] = useState(false);

  // Camera state
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraError, setCameraError] = useState("");

  const fileInputRef = useRef(null);
  const documentInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const videoRef = useRef(null);
  const cameraStreamRef = useRef(null);

  const activeChat =
    chats.find((chat) => chat.id === activeChatId) || chats[0];

  useEffect(() => {
    if (!activeChatId && chats.length > 0) {
      setActiveChatId(chats[0].id);
    }
  }, [activeChatId, chats]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeChat?.messages, loading]);

  // Stop the webcam when the component is removed.
  useEffect(() => {
    return () => {
      if (cameraStreamRef.current) {
        cameraStreamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  function createNewChat() {
    if (loading) return;

    const chat = makeChat();
    setChats((previous) => [chat, ...previous]);
    setActiveChatId(chat.id);
    setInput("");
    removeImage();
    setSelectedDocument(null);
    setAttachmentMenuOpen(false);
    inputRef.current?.focus();
  }

  function updateMessages(chatId, messages) {
    setChats((previous) =>
      previous.map((chat) =>
        chat.id === chatId ? { ...chat, messages } : chat
      )
    );
  }

  function chooseImage(event) {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) return;

    if (!["image/jpeg", "image/png"].includes(file.type)) {
      alert("Please choose a JPG or PNG image.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      alert("Please choose an image smaller than 10 MB.");
      return;
    }

    const previewUrl = URL.createObjectURL(file);

    setSelectedImage((previous) => {
      if (previous?.previewUrl) {
        URL.revokeObjectURL(previous.previewUrl);
      }

      return { file, previewUrl };
    });
    setSelectedDocument(null);
  }

  function chooseDocument(event) {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) return;

    const allowedExtensions = [
      ".pdf",
      ".txt",
      ".docx",
      ".xlsx",
      ".png",
      ".jpg",
      ".jpeg",
    ];

    const fileName = file.name.toLowerCase();
    const allowed = allowedExtensions.some((extension) =>
      fileName.endsWith(extension)
    );

    if (!allowed) {
      alert("Please choose a PDF, TXT, DOCX, XLSX, PNG, JPG, or JPEG file.");
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      alert("Please choose a file smaller than 15 MB.");
      return;
    }

    removeImage();
    setSelectedDocument(file);
    setAttachmentMenuOpen(false);
  }

  function removeImage() {
    setSelectedImage((previous) => {
      if (previous?.previewUrl) {
        URL.revokeObjectURL(previous.previewUrl);
      }
      return null;
    });
  }

  // Open the actual webcam instead of opening the file manager.
  async function openCamera() {
    setCameraError("");

    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError(
        "Camera access is unavailable. Open PRISM using http://localhost:5173 in Chrome."
      );
      setCameraOpen(true);
      return;
    }

    setCameraOpen(true);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" },
        audio: false,
      });

      cameraStreamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
    } catch (error) {
      setCameraError(
        error.name === "NotAllowedError" || error.name === "PermissionDeniedError"
          ? "Camera permission was denied. Allow camera access in Chrome site settings and try again."
          : "Could not open the webcam. Check that your camera is connected and not being used by another application."
      );
    }
  }

  function closeCamera() {
    if (cameraStreamRef.current) {
      cameraStreamRef.current.getTracks().forEach((track) => track.stop());
      cameraStreamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setCameraOpen(false);
    setCameraError("");
  }

  function capturePhoto() {
    const video = videoRef.current;

    if (!video || !video.videoWidth || !video.videoHeight) {
      setCameraError("The camera is not ready yet. Please wait and try again.");
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");

    if (!context) {
      setCameraError("Could not capture the photo. Please try again.");
      return;
    }

    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setCameraError("Could not capture the photo. Please try again.");
          return;
        }

        const photo = new File([blob], "prism-camera-photo.jpg", {
          type: "image/jpeg",
        });

        const previewUrl = URL.createObjectURL(photo);

        setSelectedImage((previous) => {
          if (previous?.previewUrl) {
            URL.revokeObjectURL(previous.previewUrl);
          }

          return { file: photo, previewUrl };
        });
        setSelectedDocument(null);

        closeCamera();
      },
      "image/jpeg",
      0.92
    );
  }

  async function sendMessage(messageText = input) {
    const text = messageText.trim();
    const image = selectedImage;
    const document = selectedDocument;
    const attachment = image?.file || document;

    if ((!text && !attachment) || loading || !activeChat) return;

    const chatId = activeChat.id;

    const userMessage = {
      id: Date.now(),
      role: "user",
      content:
        text ||
        (image ? "Please describe this image." : "Please analyze this document."),
      imageUrl: image?.previewUrl || null,
      fileName: document?.name || null,
    };

    const updatedMessages = [...activeChat.messages, userMessage];

    updateMessages(chatId, updatedMessages);

    setInput("");
    setAttachmentMenuOpen(false);
    setLoading(true);

    setChats((previous) =>
      previous.map((chat) =>
        chat.id === chatId
          ? {
              ...chat,
              title:
                chat.messages.length === 0
                  ? (text || attachment?.name || "New chat").slice(0, 35)
                  : chat.title,
            }
          : chat
      )
    );

    try {
      let response;

      if (attachment) {
        const formData = new FormData();
        formData.append(
          "question",
          text ||
            (image
              ? "Please describe this image."
              : "Please analyze this document.")
        );
        formData.append("file", attachment);
        response = await fetch("http://127.0.0.1:8000/api/infer-file", {
          method: "POST",
          body: formData,
        });
      } else {
        response = await fetch(API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: text }),
        });
      }

      if (!response.ok) {
        let message = `Backend error (${response.status})`;
        try {
          const errorData = await response.json();
          message = errorData.detail || message;
        } catch {
          // Keep the fallback error message.
        }
        throw new Error(message);
      }

      const data = await response.json();

      const assistantMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content:
          data.answer || data.response || "The backend returned no answer.",
        sensitivity: data.sensitivity,
        confidence: data.confidence,
        selectedModel: data.selected_model,
        route: data.route || data.decision,
        latency: data.latency_ms,
        explanation: data.explanation || data.reason,
        riskScore: data.risk_score,
        riskLevel: data.risk_level,
        riskReasons: data.risk_reasons || [],
        policyDecision: data.policy_decision || data.decision,
        fileName: attachment?.name || null,
      };

      setChats((previous) =>
        previous.map((chat) =>
          chat.id === chatId
            ? { ...chat, messages: [...chat.messages, assistantMessage] }
            : chat
        )
      );

      if (image?.previewUrl) {
        URL.revokeObjectURL(image.previewUrl);
      }
      setSelectedImage(null);
      setSelectedDocument(null);
    } catch (error) {
      setChats((previous) =>
        previous.map((chat) =>
          chat.id === chatId
            ? {
                ...chat,
                messages: [
                  ...chat.messages,
                  {
                    id: Date.now() + 2,
                    role: "assistant",
                    content: `Sorry, something went wrong: ${error.message}`,
                    isError: true,
                  },
                ],
              }
            : chat
        )
      );
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  function deleteChat(chatId) {
    if (loading) return;

    const remaining = chats.filter((chat) => chat.id !== chatId);

    if (remaining.length === 0) {
      const newChat = makeChat();
      setChats([newChat]);
      setActiveChatId(newChat.id);
      return;
    }

    setChats(remaining);

    if (activeChatId === chatId) {
      setActiveChatId(remaining[0].id);
    }
  }

  const filteredChats = chats.filter((chat) =>
    chat.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand">
            <div className="brand-icon">P</div>
            <span>PRISM</span>
          </div>

          <button
            className="icon-button"
            title="New chat"
            onClick={createNewChat}
          >
            ＋
          </button>
        </div>

        <button className="new-chat-button" onClick={createNewChat}>
          <span>＋</span> New chat
        </button>

        <div className="search-box">
          <span>⌕</span>
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search chats"
          />
        </div>

        <div className="sidebar-section-label">YOUR CHATS</div>

        <div className="chat-list">
          {filteredChats.map((chat) => (
            <div
              key={chat.id}
              className={`chat-list-item ${
                chat.id === activeChatId ? "active" : ""
              }`}
            >
              <button
                className="chat-title-button"
                onClick={() => {
                  if (!loading) {
                    setActiveChatId(chat.id);
                    removeImage();
                    setSelectedDocument(null);
                    setAttachmentMenuOpen(false);
                  }
                }}
              >
                <span className="chat-icon">▤</span>
                <span className="chat-title">{chat.title}</span>
              </button>

              <button
                className="delete-chat-button"
                title="Delete chat"
                onClick={() => deleteChat(chat.id)}
              >
                ×
              </button>
            </div>
          ))}

          {filteredChats.length === 0 && (
            <p className="empty-search">No chats found</p>
          )}
        </div>

        <div className="sidebar-bottom">
          <div className="profile-avatar">U</div>
          <div className="profile-details">
            <div className="profile-name">PRISM User</div>
            <div className="profile-plan">Privacy-aware AI</div>
          </div>
          <span className="profile-menu">⋯</span>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div className="topbar-title">
            <span className="mobile-brand">P</span>
            <span>New conversation</span>
            <span className="privacy-badge">
              <span className="status-dot" /> Privacy first
            </span>
          </div>
          <div className="topbar-right">Adaptive AI Router</div>
        </header>

        <section className="conversation">
          {!activeChat?.messages.length ? (
            <div className="welcome">
              <div className="welcome-icon">✳</div>
              <h1>What can I help you with?</h1>
              <p>
                Ask anything. PRISM helps route your requests with privacy
                in mind.
              </p>

            </div>
          ) : (
            <div className="messages">
              {activeChat.messages.map((message) => (
                <div
                  key={message.id}
                  className={`message-row ${message.role}`}
                >
                  {message.role === "assistant" && (
                    <div className="message-avatar">P</div>
                  )}

                  <div className="message-content">
                    {message.role === "user" && (
                      <div className="message-author">You</div>
                    )}

                    {message.imageUrl && (
                      <img
                        className="message-image"
                        src={message.imageUrl}
                        alt="Attached image"
                      />
                    )}

                    <div
                      className={`message-bubble ${
                        message.isError ? "error-bubble" : ""
                      }`}
                    >
                      {message.content}
                    </div>

                    {message.role === "assistant" && !message.isError && (
                      <div className="message-metadata">
                        {message.selectedModel && (
                          <span>Model: {message.selectedModel}</span>
                        )}
                        {message.latency != null && (
                          <span>Time: {message.latency} ms</span>
                        )}
                        {message.riskScore != null && (
                          <span>
                            Risk: {message.riskScore}/100
                            {message.riskLevel ? ` (${message.riskLevel})` : ""}
                          </span>
                        )}
                        {message.policyDecision && (
                          <span>Decision: {message.policyDecision}</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message-row assistant">
                  <div className="message-avatar">P</div>
                  <div className="message-bubble loading-bubble">
                    PRISM is thinking…
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </section>

        <footer className="composer-area">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg"
            hidden
            onChange={chooseImage}
          />

          <input
            ref={documentInputRef}
            type="file"
            accept=".pdf,.txt,.docx,.xlsx,.png,.jpg,.jpeg"
            hidden
            onChange={chooseDocument}
          />

          {selectedImage && (
            <div className="image-preview">
              <img src={selectedImage.previewUrl} alt="Selected preview" />

              <div className="image-preview-details">
                <strong>{selectedImage.file.name}</strong>
                <small>
                  {(selectedImage.file.size / 1024).toFixed(0)} KB · Image
                  selected
                </small>
              </div>

              <button
                type="button"
                className="remove-image-button"
                onClick={removeImage}
                title="Remove image"
              >
                ×
              </button>
            </div>
          )}

          {selectedDocument && (
            <div className="image-preview">
              <div className="image-preview-details">
                <strong>{selectedDocument.name}</strong>
                <small>
                  {(selectedDocument.size / 1024).toFixed(0)} KB · Document
                  selected
                </small>
              </div>

              <button
                type="button"
                className="remove-image-button"
                onClick={() => setSelectedDocument(null)}
                title="Remove document"
              >
                ×
              </button>
            </div>
          )}

          <div className="composer">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message PRISM..."
              rows={1}
              disabled={loading}
            />

            <div className="composer-bottom">
              <div className="composer-tools">
                <div className="attachment-wrapper">
                  <button
                    type="button"
                    className="composer-tool"
                    title="Add photos and files"
                    aria-expanded={attachmentMenuOpen}
                    onClick={() =>
                      setAttachmentMenuOpen((open) => !open)
                    }
                    disabled={loading}
                  >
                    ＋
                  </button>

                  {attachmentMenuOpen && (
                    <>
                      <button
                        type="button"
                        className="attachment-backdrop"
                        aria-label="Close attachment menu"
                        onClick={() => setAttachmentMenuOpen(false)}
                      />

                      <div className="attachment-menu">
                        <button
                          type="button"
                          className="attachment-option"
                          onClick={() => {
                            setAttachmentMenuOpen(false);
                            fileInputRef.current?.click();
                          }}
                        >
                          <span className="attachment-option-icon">▧</span>
                          <span>
                            <strong>Upload photos</strong>
                            <small>JPG, PNG</small>
                          </span>
                        </button>

                        <button
                          type="button"
                          className="attachment-option"
                          onClick={() => {
                            setAttachmentMenuOpen(false);
                            openCamera();
                          }}
                        >
                          <span className="attachment-option-icon">📷</span>
                          <span>
                            <strong>Take a photo</strong>
                            <small>Use your webcam</small>
                          </span>
                        </button>

                        <button
                          type="button"
                          className="attachment-option"
                          onClick={() => {
                            setAttachmentMenuOpen(false);
                            documentInputRef.current?.click();
                          }}
                        >
                          <span className="attachment-option-icon">▤</span>
                          <span>
                            <strong>Upload files</strong>
                            <small>PDF, TXT, DOCX and more</small>
                          </span>
                        </button>
                      </div>
                    </>
                  )}
                </div>

                <span className="composer-hint">
                  {selectedImage
                    ? "Image attached"
                    : selectedDocument
                      ? "Document attached"
                      : "Enter to send · Shift + Enter for a new line"}
                </span>
              </div>

              <button
                type="button"
                className="send-button"
                title="Send message"
                onClick={() => sendMessage()}
                disabled={
                  loading ||
                  (!input.trim() && !selectedImage && !selectedDocument)
                }
              >
                {loading ? "…" : "↑"}
              </button>
            </div>
          </div>

          <p className="composer-disclaimer">
            PRISM may make mistakes. Check important information.
          </p>
        </footer>
      </main>

      {cameraOpen && (
        <div
          className="camera-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="Take a photo"
        >
          <div className="camera-dialog">
            <div className="camera-header">
              <h3>Take a photo</h3>

              <button
                type="button"
                className="camera-close"
                onClick={closeCamera}
                aria-label="Close camera"
              >
                ✕
              </button>
            </div>

            {cameraError ? (
              <p className="camera-error">{cameraError}</p>
            ) : (
              <video
                ref={videoRef}
                className="camera-video"
                autoPlay
                playsInline
                muted
              />
            )}

            <div className="camera-actions">
              <button type="button" onClick={closeCamera}>
                Cancel
              </button>

              <button
                type="button"
                className="camera-capture"
                onClick={capturePhoto}
                disabled={Boolean(cameraError)}
              >
                Capture photo
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
