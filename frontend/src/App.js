import { useState, useRef, useEffect } from "react";

// backend base URL (override by creating frontend/.env with REACT_APP_API_URL=...)
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5050";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // crisis flag state
  const [crisisLevel, setCrisisLevel] = useState("none");

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, crisisLevel]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userText = input;

    // add user message immediately
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setInput("");
    setLoading(true);

    try {
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

      // read safety_level from backend response
      const level = data?.safety_level || "none";
      setCrisisLevel(level);

      // add assistant reply
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply },
      ]);
    } catch (err) {
      setCrisisLevel("none");
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

  const bannerStyles =
    crisisLevel === "imminent"
      ? "border-red-300 bg-red-50"
      : "border-yellow-300 bg-yellow-50";

  const bannerTitle =
    crisisLevel === "imminent" ? "Crisis resources" : "Support resources";

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <header className="p-4 bg-purple-600 text-white text-center text-xl font-semibold">
        Mental Health Support Chatbot
      </header>

      {/* crisis banner driven by backend safety_level */}
      {crisisLevel !== "none" && (
        <div className={`mx-4 mt-3 p-3 rounded-lg border ${bannerStyles}`}>
          <div className="font-semibold">{bannerTitle}</div>
          <div className="text-sm">
            If you’re in immediate danger, call local emergency services. In the
            U.S., call or text <b>988</b> (Suicide &amp; Crisis Lifeline).
          </div>
          <button
            className="mt-2 text-sm underline"
            onClick={() => setCrisisLevel("none")}
          >
            Dismiss
          </button>
        </div>
      )}

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
