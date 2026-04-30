import React, { useState } from 'react';

const ChatAssist = ({ regionId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    const userMsg = { role: 'user', content: message };
    setHistory(prev => [...prev, userMsg]);
    setMessage('');
    setLoading(true);

    try {
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, region_id: regionId })
      });
      const data = await response.json();
      
      const aiMsg = { role: 'ai', data };
      setHistory(prev => [...prev, aiMsg]);
    } catch (err) {
      console.error("Chat failed:", err);
      setHistory(prev => [...prev, { role: 'ai', error: 'Assistant unavailable.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`chat-assist-panel ${isOpen ? 'open' : ''}`}>
      <button className="chat-toggle" onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? '✕ Close Assistant' : '💬 Need Help? Ask AI'}
      </button>

      {isOpen && (
        <div className="chat-window">
          <div className="chat-header">
            <h3>Election Assistant</h3>
            <p>Ask about parties, policies, or the process.</p>
          </div>

          <div className="chat-messages">
            {history.length === 0 && (
              <p className="chat-placeholder">Try asking: "What are the healthcare policies?"</p>
            )}
            {history.map((msg, i) => (
              <div key={i} className={`chat-bubble ${msg.role}`}>
                {msg.role === 'user' ? (
                  <p>{msg.content}</p>
                ) : msg.error ? (
                  <p style={{ color: '#ef4444' }}>{msg.error}</p>
                ) : (
                  <div className="ai-response">
                    <p><strong>Focus:</strong> {msg.data.intent}</p>
                    <div className="party-comparison">
                      {msg.data.parties.map((p, j) => (
                        <div key={j} className="party-match">
                          <strong>{p.name}</strong>
                          <ul>
                            {p.matching_policies.map((pol, k) => (
                              <li key={k}>{pol}</li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                    <p className="chat-disclaimer">{msg.data.disclaimer}</p>
                  </div>
                )}
              </div>
            ))}
            {loading && <div className="chat-bubble ai loading">Analyzing priorities...</div>}
          </div>

          <form className="chat-input" onSubmit={handleSend}>
            <input 
              type="text" 
              placeholder="Type your priority..." 
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              disabled={loading}
            />
            <button type="submit" disabled={loading}>Send</button>
          </form>
        </div>
      )}
    </div>
  );
};

export default ChatAssist;
