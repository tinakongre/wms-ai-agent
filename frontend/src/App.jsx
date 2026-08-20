import { useState } from "react";
import "./App.css";

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);

  const sendMessage = async () => {
    if (!question.trim()) return;

    const userMessage = {
      role: "user",
      content: question,
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question,
        }),
      });

      const data = await response.json();

      const aiMessage = {
        role: "assistant",
        content: data.answer || data.message || "I couldn't find an answer.",
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Unable to connect to the WMS AI Agent.",
        },
      ]);
    }

    setQuestion("");
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      sendMessage();
    }
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-icon">W</div>
          <div>
            <h2>WMS AI</h2>
            <span>Warehouse Intelligence</span>
          </div>
        </div>

        <nav>
          <button className="nav-item active">💬 AI Chat</button>
          <button className="nav-item">📦 Inventory</button>
          <button className="nav-item">📄 Documents</button>
        </nav>

        <div className="sidebar-bottom">
          <div className="status">
            <span className="status-dot"></span>
            System Online
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="header">
          <div>
            <h1>Warehouse Management System</h1>
            <p>Ask questions about your inventory and warehouse operations.</p>
          </div>

          <div className="header-badge">
            <span>●</span> AI Ready
          </div>
        </header>

        <section className="chat-container">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-icon">🤖</div>

              <h2>How can I help?</h2>

              <p>
                Ask me about inventory, stock levels, warehouses,
                or reorder requirements.
              </p>

              <div className="suggestions">
                <button
                  onClick={() =>
                    setQuestion("How many LED Monitors do we have?")
                  }
                >
                  How many LED Monitors do we have?
                </button>

                <button
                  onClick={() =>
                    setQuestion("Which products are running low?")
                  }
                >
                  Which products are running low?
                </button>

                <button
                  onClick={() =>
                    setQuestion("What products are in warehouse W01?")
                  }
                >
                  What's in warehouse W01?
                </button>
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`message ${
                    message.role === "user" ? "user-message" : "ai-message"
                  }`}
                >
                  <div className="message-avatar">
                    {message.role === "user" ? "You" : "AI"}
                  </div>

                  <div className="message-content">
                    {message.content}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <div className="input-area">
          <div className="input-wrapper">
            <input
              type="text"
              placeholder="Ask about your warehouse..."
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleKeyDown}
            />

            <button className="send-button" onClick={sendMessage}>
              ➤
            </button>
          </div>

          <p className="input-note">
            WMS AI can answer questions using your inventory and warehouse knowledge.
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;