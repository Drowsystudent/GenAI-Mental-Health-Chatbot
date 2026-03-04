import { useState, useRef, useEffect } from "react";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5050";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [crisisLevel, setCrisisLevel] = useState("none");

  // NEW: crisis popup state
  const [showCrisisPopup, setShowCrisisPopup] = useState(false);

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, crisisLevel]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userText = input;

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

      const level = data?.safety_level || "none";
      setCrisisLevel(level);

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
    <div className="flex flex-col h-screen bg-gray-100 relative">
      <header className="p-4 bg-purple-600 text-white text-center text-xl font-semibold">
        Mental Health Support Chatbot
      </header>

      {crisisLevel !== "none" && (
        <div className={`mx-4 mt-3 p-3 rounded-lg border ${bannerStyles}`}>
          <div className="font-semibold">{bannerTitle}</div>
          <div className="text-sm">
            If you’re in immediate danger, call local emergency services. In the
            U.S., call or text <b>988</b>.
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

      {/* NEW Bubble Footer */}
      <footer className="p-4 bg-white">
        <div className="flex items-center bg-gray-100 rounded-full px-4 py-2 shadow-inner">
          
          {/* Crisis Button */}
          <button
            onClick={() => setShowCrisisPopup(true)}
            className="flex items-center gap-1 text-sm bg-red-100 text-red-600 px-3 py-1 rounded-full mr-2"
          >
            📄 Crisis
          </button>

          {/* Input */}
          <input
            className="flex-1 bg-transparent focus:outline-none px-2"
            placeholder="What's on your mind?"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />

          {/* Send Button */}
          <button
            className="ml-2 bg-blue-500 text-white px-4 py-2 rounded-full disabled:opacity-50"
            onClick={sendMessage}
            disabled={loading}
          >
            Send
          </button>
        </div>
      </footer>

      {/* CRISIS POPUP OVERLAY */}
      {showCrisisPopup && (
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white w-11/12 max-w-md rounded-2xl p-6 relative shadow-lg">
            
            {/* Close Button */}
            <button
              onClick={() => setShowCrisisPopup(false)}
              className="absolute top-3 right-4 text-gray-500 text-xl"
            >
              ✕
            </button>

            <h2 className="text-xl font-semibold mb-2">
              Crisis Resources
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              If you are currently in crisis or need immediate help, use these 24/7 resources for help.
            </p>

            <div className="space-y-3">

              <div className="bg-gray-100 p-3 rounded-xl">
                <strong>Suicide & Crisis Lifeline</strong><br/>
                Call <b>988</b>
              </div>

              <div className="bg-gray-100 p-3 rounded-xl">
                <strong>Crisis Text Line</strong><br/>
                Text <b>HELLO</b> to <b>741741</b>
              </div>

              <div className="bg-gray-100 p-3 rounded-xl">
                <strong>Domestic Violence Hotline</strong><br/>
                Call <b>1-800-799-SAFE (7233)</b><br/>
                Text <b>START</b> to <b>88788</b>
              </div>

            </div>
          </div>
        </div>
      )}
    </div>
  );
}
