import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import ChatAssist from '../components/ChatAssist';

const Journey = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stepData, setStepData] = useState(null);
  const [extraData, setExtraData] = useState(null); // Elections/Parties data
  const [showToast, setShowToast] = useState(false);
  const [simIndex, setSimIndex] = useState(0);


  const userId = localStorage.getItem('votai_user_id');
  const userAge = parseInt(localStorage.getItem('votai_user_age') || '0');
  const regionId = localStorage.getItem('votai_region_id') || 'IN-MH';
  const regionName = localStorage.getItem('votai_region_name') || 'Default';

  const isUnderage = userAge < 18;

  useEffect(() => {
    if (!userId) {
      navigate('/');
      return;
    }
    fetchStep();
  }, [userId]);

  const fetchStep = async (message = null) => {
    try {
      setLoading(true);
      const data = await api.getCurrentStep(userId, regionId, message);

      if (!data || !data.current_step) {
        console.error("DEBUG: Malformed step data:", data);
        throw new Error("Invalid response from server: Missing step information.");
      }

      setStepData(data);
      setError(null);
      console.log("DEBUG: Journey API Response:", data);

      // Fetch context-specific data based on step
      const stepNum = data.current_step.step_number;
      if (stepNum === 2) {
        const election = await api.getTimeline(regionId);
        setExtraData(election.timeline);
      } else if (stepNum === 4) {
        const parties = await api.getParties(regionId);
        setExtraData(parties);
      } else {
        setExtraData(null);
      }

    } catch (err) {
      console.error("Connecting to civic system...", err);
      setError(err.message || "Connecting to civic system...");
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async () => {
    try {
      setLoading(true);
      await api.advanceStep(userId);
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000);
      await fetchStep();
    } catch (err) {
      console.error("Advancement failed:", err);
      alert("Failed to move to next step.");
    } finally {
      setLoading(false);
    }
  };

  if (loading && !stepData) return <div className="page"><p>Loading your journey...</p></div>;
  if (error) return (
    <div className="page" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
      <p style={{ color: '#ef4444', marginBottom: '1.5rem' }}>{error}</p>
      <button onClick={() => fetchStep()} className="btn-secondary">Retry Loading</button>
    </div>
  );

  if (!stepData) {
    return (
      <div className="page">
        <p>⚠️ No step data received</p>
      </div>
    );
  }

  const { current_step, explanation, action_items, completed, message: completionMessage } = stepData;
  const readiness = current_step.percentage || 0;
  const isFinished = completed || current_step.step_number > 5;

  console.log("DEBUG: Journey Render - Step:", current_step.step_number, "Ready:", readiness, "Finished:", isFinished);

  // ── Step-Specific UI Renderers ─────────────────────────────────────────────

  const renderStepContent = () => {
    const sn = current_step.step_number;

    if (sn === 1) return (
      <div className="checklist">
        <label className="checkbox-group" style={{ marginBottom: '0.5rem' }}>
          <input type="checkbox" checked={userAge >= 18} readOnly />
          <span>I am 18 years or older</span>
        </label>
        <label className="checkbox-group">
          <input type="checkbox" checked={true} readOnly />
          <span>I am a citizen of {localStorage.getItem('votai_country') || 'this country'}</span>
        </label>
      </div>
    );

    if (sn === 2) {
      return (
        <div style={{ marginTop: "1.5rem" }}>
          <h3>📄 What you need</h3>

          <ul>
            <li>✔ Valid ID proof (Aadhaar / Passport)</li>
            <li>✔ Address proof</li>
            <li>✔ Passport size photo</li>
          </ul>

          <button
            style={{ marginTop: "1rem" }}
            onClick={() => window.open("https://voters.eci.gov.in/", "_blank")}
          >
            Open Official Portal ↗
          </button>
        </div>
      );
    }

    // 🔧 STEP 3 — Verification
    if (sn === 3) {
      return (
        <div style={{ marginTop: "1.5rem" }}>
          <h3>🔧 Quick Services</h3>

          <div
            className="service-card"
            style={{
              cursor: "pointer",
              padding: "12px",
              borderRadius: "10px",
              background: "#1e293b",
              marginTop: "10px",
              border: "1px solid #334155"
            }}
            onClick={() => window.open("https://electoralsearch.eci.gov.in/", "_blank")}
          >
            🔍 Search your name in voter list
          </div>

          <div
            className="service-card"
            style={{
              cursor: "pointer",
              padding: "12px",
              borderRadius: "10px",
              background: "#1e293b",
              marginTop: "10px",
              border: "1px solid #334155"
            }}
            onClick={() => window.open("https://voters.eci.gov.in/", "_blank")}
          >
            📝 Register as new voter (Form 6)
          </div>

          <div
            className="service-card"
            style={{
              cursor: "pointer",
              padding: "12px",
              borderRadius: "10px",
              background: "#1e293b",
              marginTop: "10px",
              border: "1px solid #334155"
            }}
            onClick={() => window.open("https://voters.eci.gov.in/", "_blank")}
          >
            ✏️ Correct your details (Form 8)
          </div>
        </div>
      );
    }

    if (sn === 4) {
      const parties = extraData?.parties || [];
      return (
        <div className="party-preview">
          <div className="party-grid">
            {parties.length > 0 ? parties.slice(0, 3).map(p => (
              <div key={p.party_id} className="party-mini-card">
                <h4>{p.name || "Unknown Party"}</h4>
                <div className="tag-container">
                  {(p.focus_areas || []).slice(0, 2).map(tag => <span key={tag} className="tag">{tag}</span>)}
                </div>
              </div>
            )) : <p>No party data available for this region.</p>}
          </div>
          <button onClick={() => navigate('/parties')} className="expand-link" style={{ marginTop: '1rem' }}>
            View all parties & full policies
          </button>
        </div>
      );
    }

    if (sn === 5) {
      const steps = current_step.simulation_steps || [
        { title: "Arrival", desc: "Go to polling booth" },
        { title: "Verification", desc: "Show ID" },
        { title: "Voting", desc: "Use EVM" },
        { title: "Exit", desc: "Ink mark applied" }
      ];

      return (
        <div style={{ marginTop: "2rem" }}>
          <h3>🗳️ Voting Simulation</h3>

          <p>Step {simIndex + 1} of {steps.length}</p>

          <h4>{steps[simIndex].title}</h4>
          <p>{steps[simIndex].desc}</p>

          <div style={{ marginTop: "1rem" }}>
            {simIndex > 0 && (
              <button onClick={() => setSimIndex(simIndex - 1)}>
                ⬅ Back
              </button>
            )}

            {simIndex < steps.length - 1 ? (
              <button onClick={() => setSimIndex(simIndex + 1)}>
                Next ➡
              </button>
            ) : (
              <div style={{ color: "green", marginTop: "1rem" }}>
                🎉 You have completed the voting simulation!
              </div>
            )}
          </div>
        </div>
      );
    }

    return null;
  };

  // 🎉 COMPLETION SCREEN
  if (completed) {
    return (
      <div className="page">
        <h1>{completionMessage || "You are ready to vote!"}</h1>
        <p>You are fully prepared for voting.</p>
        <button onClick={() => navigate('/')} className="btn-secondary" style={{ marginTop: '2rem' }}>
          Back to Home
        </button>
      </div>
    );
  }


  return (
    <div className="page">
      <div className="journey-container">

        {/* Readiness Section */}
        <div className="readiness-banner">
          <div className="readiness-header">
            <span>{regionName} Election Journey</span>
            <span className="readiness-text">{readiness}% Ready</span>
          </div>
          <div className="progress-bar-container">
            <div className="progress-bar-fill" style={{ width: `${readiness}%` }}></div>
          </div>
        </div>

        {isFinished ? (
          <div className="step-card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
            <h1 style={{ fontSize: '3rem' }}>🎉</h1>
            <h1>{completionMessage || "You are ready to vote!"}</h1>
            <p style={{ color: '#94a3b8', marginTop: '1rem' }}>
              You have completed all guidance steps. You are now an informed voter.
            </p>
            <button onClick={() => navigate('/ready')} className="btn-primary" style={{ marginTop: '2rem' }}>
              View Final Checklist
            </button>
          </div>
        ) : (
          <>
            {isUnderage && (
              <div className="alert-deadline">
                <span>👶</span>
                <span><strong>Note:</strong> You are not eligible to vote yet, but you can explore.</span>
              </div>
            )}

            <div className="step-card">
              <span className="step-badge">Step {current_step.step_number} of 5</span>
              <h1>{current_step.step_name}</h1>

              <div style={{ margin: '1.5rem 0' }}>
                <h4 style={{ color: '#64748b', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>What this means</h4>
                <p style={{ color: '#cbd5e1', marginTop: '0.5rem', lineHeight: '1.6' }}>{explanation || current_step.description}</p>
              </div>

              {renderStepContent()}

              <div style={{ marginTop: '2rem' }}>
                <h4 style={{ color: '#64748b', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>What you should do</h4>
                <ul className="action-list">
                  {(action_items || []).map((action, index) => (
                    <li key={index} className="action-item">
                      <span className="action-bullet">→</span>
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {action_items && action_items.length > 0 && (
                <div className="next-action-footer">
                  <strong>👉 Next Action</strong>
                  <span>{action_items[0]}</span>
                </div>
              )}

              <button
                onClick={handleComplete}
                className="btn-primary"
                disabled={loading || isUnderage}
                style={{ marginTop: '2rem' }}
              >
                {loading ? "Processing..." : isUnderage ? "Action Disabled (Minor)" : "Mark Done & Continue"}
              </button>
            </div>

            <div className="quick-actions">
              <button className="btn-secondary" onClick={() => fetchStep("I moved recently")}>I moved recently</button>
              <button className="btn-secondary" onClick={() => fetchStep("I missed deadline")}>I missed deadline</button>
              <button className="btn-secondary" onClick={() => fetchStep("My name isn't on list")}>Name missing</button>
            </div>
          </>
        )}

        {showToast && <div className="feedback-toast">✔ Step completed</div>}

        {/* Chat Assistant */}
        <ChatAssist regionId={regionId} step={current_step.step_number} />
      </div>
    </div>
  );
};

export default Journey;
