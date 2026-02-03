import { useState, useRef, useEffect } from "react";

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

    setMessages((prev) => [...prev, { role: "user", content: input }]);
    setInput("");
    setLoading(true);

    try {
      /* ===== REAL BACKEND (ENABLE LATER) ===== */
      /*
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      const data = await res.json();
      */

      /* ===== MOCK BACKEND ===== */
      await new Promise((res) => setTimeout(res, 1200));
      const data = {
        reply: "This is a mock response for the prototype. I’m here to listen.",
      };

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, something went wrong.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-full max-w-2xl bg-white shadow-lg rounded-xl flex flex-col h-[80vh]">
        <header className="p-4 border-b text-center font-semibold text-lg">
          GenAI Mental Health Chatbot
        </header>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`max-w-[75%] px-4 py-2 rounded-lg text-sm ${
                m.role === "user"
                  ? "bg-user ml-auto text-right"
                  : "bg-bot mr-auto"
              }`}
            >
              {m.content}
            </div>
          ))}

          {loading && (
            <div className="bg-bot px-4 py-2 rounded-lg text-sm w-fit">
              Typing…
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="p-4 border-t flex gap-2">
          <input
            className="flex-1 border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="Type your message…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button
            onClick={sendMessage}
            className="bg-primary text-white px-4 py-2 rounded-lg hover:opacity-90"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
