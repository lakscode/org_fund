import { useState, useRef, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";

/* const SAMPLE_QUESTIONS = [
  "What is our portfolio NOI YTD and how does it compare to budget?",
  "Show me the property portfolio overview by type and market.",
  "What is the current DSCR across our funds?",
  "Show me the top expense variance drivers across the portfolio.",
  "Give me tenant and lease overview.",
  "Summarize fund performance including returns.",
]; */

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function Chat() {
  const { currentOrg } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || !currentOrg || loading) return;
    const userMsg: Message = { role: "user", content: text.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.post(`/orgs/${currentOrg.id}/chat`, { message: text.trim() });
      setMessages((prev) => [...prev, { role: "assistant", content: res.data.response }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, something went wrong. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  if (!currentOrg) return <p>No organization selected.</p>;

  // Simple markdown-like rendering for **bold** and line breaks
  const renderContent = (text: string) => {
    const lines = text.split("\n");
    return lines.map((line, i) => {
      const parts = line.split(/(\*\*[^*]+\*\*)/g).map((part, j) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return <strong key={j}>{part.slice(2, -2)}</strong>;
        }
        // Handle *italic*
        const italicParts = part.split(/(\*[^*]+\*)/g).map((ip, k) => {
          if (ip.startsWith("*") && ip.endsWith("*")) {
            return <em key={k}>{ip.slice(1, -1)}</em>;
          }
          return ip;
        });
        return <span key={j}>{italicParts}</span>;
      });
      return (
        <span key={i}>
          {parts}
          {i < lines.length - 1 && <br />}
        </span>
      );
    });
  };

  return (
    <div className="chat-page page-container">
      <div className="chat-header">
        <h2 className="page-title">REstackAI Chat</h2>
        <p className="page-subtitle">Ask questions about your portfolio using governed metrics</p>
      </div>

      <div className="chat-body">
        <div className="chat-main">
          {messages.length === 0 ? (
            <div className="chat-welcome">
              <div className="chat-welcome-icon">&#9993;</div>
              <h3>Ask REstackAI</h3>
              <p>
                Get answers about your portfolio using governed metrics. All responses
                cite their data source, time period, and metric definition.
              </p>
              {/* <div className="chat-suggestions">
                {SAMPLE_QUESTIONS.map((q, i) => (
                  <button key={i} className="chat-suggestion" onClick={() => sendMessage(q)}>
                    {q}
                  </button>
                ))}
              </div> */}
            </div>
          ) : (
            <div className="chat-messages">
              {messages.map((msg, i) => (
                <div key={i} className={`chat-msg chat-msg-${msg.role}`}>
                  <div className="chat-msg-bubble">{renderContent(msg.content)}</div>
                </div>
              ))}
              {loading && (
                <div className="chat-msg chat-msg-assistant">
                  <div className="chat-msg-bubble chat-typing">Analyzing your portfolio data...</div>
                </div>
              )}
              <div ref={messagesEnd} />
            </div>
          )}

          <form className="chat-input-bar" onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Ask about your portfolio..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
            />
            <button type="submit" className="chat-send-btn" disabled={loading}>&#9654;</button>
          </form>
        </div>

        <aside className="chat-context" style={{display:'none'}}>
          <h4>ACTIVE CONTEXT</h4>
          <div className="chat-context-item">
            <span className="chat-context-label">Entity</span>
            <span className="chat-context-value">{currentOrg.name}</span>
          </div>
          <div className="chat-context-item">
            <span className="chat-context-label">Time Period</span>
            <span className="chat-context-value">YTD &middot; Jan 2026</span>
          </div>
          <div className="chat-context-item">
            <span className="chat-context-label">Data Sources</span>
            <span className="chat-context-value">GL &middot; Leases &middot; Appraisals &middot; Bank Feeds</span>
          </div>
          <div className="chat-context-item">
            <span className="chat-context-label">AI Model</span>
            <span className="chat-context-value">Governed &middot; Source-cited</span>
          </div>
        </aside>
      </div>
    </div>
  );
}
