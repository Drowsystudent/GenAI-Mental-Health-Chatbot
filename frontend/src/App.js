import { useState, useRef, useEffect } from "react";

// configure backend base URL
// for local dev: start Flask on http://localhost:5050
// LAST RESORT: we can try overriding with REACT_APP_API_URL (creating frontend/.env)
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5050";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userText = input;

    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setInput("");
    setLoading(true);

    try {
      /* ===== REAL BACKEND ===== */
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText }),
      });

      const data = await res.json();

      if (!res.ok) {
        const msg = data?.error || "Sorry, something went wrong.";
        throw new Error(msg);
      }

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: err?.message || "Sorry, something went wrong.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <header className="p-4 bg-purple-600 text-white text-center text-xl font-semibold">
        Mental Health Support Chatbot
      </header>

      <main className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`max-w-lg p-3 rounded-lg ${
              msg.role === "user"
                ? "bg-blue-500 text-white ml-auto"
                : "bg-white text-gray-800 mr-auto"
            }`}
          >
            {msg.content}
          </div>
        ))}

        {loading && (
          <div className="max-w-lg p-3 rounded-lg bg-white text-gray-800 mr-auto">
            Typing...
          </div>
        )}

        <div ref={bottomRef} />
      </main>

      <footer className="p-4 bg-white flex gap-2">
        <input
          className="flex-1 border rounded-lg p-2 focus:outline-none"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button
          className="bg-purple-600 text-white px-4 py-2 rounded-lg disabled:opacity-50"
          onClick={sendMessage}
          disabled={loading}
        >
          Send
        </button>
      </footer>
    </div>
  );
}
