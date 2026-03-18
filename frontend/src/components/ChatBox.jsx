import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Send, Bot, User, Loader2, ShieldAlert, ThumbsUp, ThumbsDown } from "lucide-react";

export default function ChatBox({ activeSession, onSessionCreated }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [feedbackStatus, setFeedbackStatus] = useState({}); // { index: 'up' | 'down' }
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => { scrollToBottom(); }, [messages, isLoading]);

  useEffect(() => {
    if (activeSession) {
      fetchChatHistory(activeSession);
    } else {
      setMessages([]);
    }
  }, [activeSession]);

  const fetchChatHistory = async (sessionId) => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`http://127.0.0.1:8002/api/v1/dashboard/sessions/${sessionId}/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages.map(m => ({
          id: m.id,
          role: m.role,
          content: m.content,
          category: m.category || "General",
          agent_tier: m.agent_tier || "L1"
        })));
      }
    } catch (error) {
      console.error("Failed to load chat history:", error);
    }
  };

  const handleSendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { role: "user", content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("http://127.0.0.1:8003/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ message: userMessage.content, session_id: activeSession || null })
      });

      if (!res.ok) throw new Error("API error");
      const data = await res.json();

      if (!activeSession && data.session_id) onSessionCreated(data.session_id);

      setMessages(prev => [...prev, {
        id: data.message_id,
        role: "assistant",
        content: data.response,
        category: data.category,
        agent_tier: data.agent_tier
      }]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "⚠️ Failed to reach the AI agents. Please check if the backend is running and try again."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = async (idx, helpful) => {
    if (!activeSession) return;

    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("http://127.0.0.1:8003/api/v1/agents/feedback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          session_id: activeSession,
          message_id: messages[idx].id,
          helpful,
          comment: "",
          agent_tier: messages[idx].agent_tier || "L1",
          incident_category: messages[idx].category || "General"
        })
      });
      if (res.ok) {
        setFeedbackStatus(prev => ({ ...prev, [idx]: helpful ? 'up' : 'down' }));
      }
    } catch (error) {
      console.error("Feedback error:", error);
    }
  };

  return (
    <div className="chat-wrapper">
      {/* Header */}
      <div className="chat-header-bar">
        <ShieldAlert size={18} />
        <div>
          <div className="fw-semibold" style={{ fontSize: "0.9rem" }}>Incident Assistant</div>
          <div className="text-muted-custom" style={{ fontSize: "0.7rem" }}>L1 · L2 · RCA agents</div>
        </div>
        <div className="ms-auto"><div className="pulse-dot" /></div>
      </div>

      {/* Messages */}
      <div className="chat-body">
        {messages.length === 0 && !isLoading && (
          <div className="empty-state-custom">
            <div className="empty-icon-box">
              <Bot size={26} />
            </div>
            <h5 className="fw-semibold mb-2">How can I help you?</h5>
            <p className="text-muted-custom small mb-0" style={{ maxWidth: 320 }}>
              Describe your incident, paste error logs, or ask about common system issues.
            </p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`msg-row ${msg.role === "user" ? "msg-user" : "msg-agent"}`}>
            <div className="msg-avatar">
              {msg.role === "user" ? <User size={14} /> : <Bot size={14} />}
            </div>
            <div className="msg-bubble-container">
              <div className="msg-bubble">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
              </div>
              {msg.role === "assistant" && (
                <div className="msg-feedback">
                  <button
                    className={`feedback-btn ${feedbackStatus[idx] === 'up' ? 'active' : ''}`}
                    onClick={() => handleFeedback(idx, true)}
                    disabled={feedbackStatus[idx]}
                  >
                    <ThumbsUp size={12} />
                  </button>
                  <button
                    className={`feedback-btn ${feedbackStatus[idx] === 'down' ? 'active' : ''}`}
                    onClick={() => handleFeedback(idx, false)}
                    disabled={feedbackStatus[idx]}
                  >
                    <ThumbsDown size={12} />
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="msg-row msg-agent">
            <div className="msg-avatar"><Bot size={14} /></div>
            <div className="msg-bubble">
              <div className="d-flex align-items-center gap-2 text-muted-custom" style={{ fontSize: "0.82rem" }}>
                <Loader2 className="spin" size={15} />
                <span>Analyzing incident...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="chat-input-bar">
        <form className="chat-input-box" onSubmit={handleSendMessage}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe your issue... (e.g. Server throws 504 Gateway Timeout)"
            rows="2"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSendMessage(); }
            }}
          />
          <button type="submit" className="chat-send-btn" disabled={!input.trim() || isLoading}>
            <Send size={15} />
          </button>
        </form>
        <p className="text-center text-muted-custom mt-2 mb-0" style={{ fontSize: "0.68rem" }}>
          AI agents can make mistakes. Always verify critical configurations.
        </p>
      </div>
    </div>
  );
}