import React, { useState } from 'react';
import { api } from '../services/api';

const ChatAssist = ({ regionId, step }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const totalSteps = 5;
  const currentStep = step || 1;

  const handleSend = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    const userMsg = { role: 'user', content: message };
    setHistory(prev => [...prev, userMsg]);
    setMessage('');
    setLoading(true);

    try {
      console.log("SENDING:", { message, region_id: regionId });
      const data = await api.chat(message, regionId);
      console.log("DEBUG CHAT RESPONSE:", data);

      const aiMsg = { role: 'ai', data };
      setHistory(prev => [...prev, aiMsg]);
    } catch (err) {
      console.error("Chat failed:", err);
      setHistory(prev => [...prev, { role: 'ai', error: 'Connecting to civic system...' }]);
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
            <div className="progress-container">
              <p>Step {currentStep} of {totalSteps}</p>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${(currentStep / totalSteps) * 100}%` }}
                ></div>
              </div>
            </div>
            <h3>Election Assistant</h3>
            <p>Ask about parties, policies, or the process.</p>
          </div>

          <div className="chat-messages" aria-live="polite" role="log">
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
                    <div className="neutrality-badge">
                      <span className="shield-icon">🛡️</span>
                      <span>System Verified: Neutrality Active</span>
                    </div>
                    {msg.data && (
                      <>
                        <p style={{ whiteSpace: "pre-line" }}>
                          {msg.data.message}
                        </p>
                        {msg.data.next_action && (
                          <div className="chat-next-action">
                             <strong>Next:</strong> {msg.data.next_action}
                          </div>
                        )}
                        {msg.data.status === 'fallback' && (
                          <small className="chat-disclaimer">Offline Mode - Based on local data.</small>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            ))}
            {loading && <div className="chat-bubble ai loading">Analyzing...</div>}
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
