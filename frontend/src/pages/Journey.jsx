import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

const Journey = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stepData, setStepData] = useState(null);
  const [showToast, setShowToast] = useState(false);
  
  const userId = localStorage.getItem('votai_user_id');
  const userAge = parseInt(localStorage.getItem('votai_user_age') || '0');
  const regionId = localStorage.getItem('votai_region_id') || 'IN-MH'; // Fallback added
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
      setStepData(data);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch step:", err);
      setError(err.message || "Could not load your journey. Please try again.");
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
  if (!stepData) return null;

  const { current_step, explanation, action_items } = stepData;
  const readiness = current_step.percentage || 0;
  const isFinished = current_step.step_number > 5;

  return (
    <div className="page">
      <div className="journey-container">
        
        {/* Readiness Section */}
        <div className="readiness-banner">
          <div className="readiness-header">
            <span>{regionName} Election Journey</span>
            <span className="readiness-text">You are {readiness}% ready</span>
          </div>
          <div className="progress-bar-container">
            <div 
              className="progress-bar-fill" 
              style={{ width: `${readiness}%` }}
            ></div>
          </div>
        </div>

        {isFinished ? (
          <div className="step-card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎉</h1>
            <h1>You are ready to vote!</h1>
            <p style={{ color: '#94a3b8', fontSize: '1.1rem', marginBottom: '2rem' }}>
              You've completed all the steps. You're now an informed and registered voter.
            </p>
            <button onClick={() => navigate('/ready')} className="btn-primary">
              View Final Checklist
            </button>
          </div>
        ) : (
          <>
            {/* Alerts */}
            <div className="alert-deadline">
              <span>{isUnderage ? "👶" : "ℹ️"}</span>
              <span>
                <strong>Status:</strong> {isUnderage 
                  ? "You are not eligible to vote yet, but you can explore the process." 
                  : `Current Goal: ${current_step.step_name}`}
              </span>
            </div>

            {/* Step Card */}
            <div className="step-card">
              <span className="step-badge">Step {current_step.step_number} of 5</span>
              <h1>{current_step.step_name}</h1>
              <p style={{ color: '#94a3b8' }}>{current_step.description}</p>

              {explanation && (
                <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', borderLeft: '3px solid var(--primary-color)' }}>
                  <p>{explanation}</p>
                </div>
              )}

              <ul className="action-list">
                {(action_items || []).map((action, index) => (
                  <li key={index} className="action-item">
                    <span className="action-bullet">→</span>
                    <span>{action}</span>
                  </li>
                ))}
              </ul>

              <button 
                onClick={handleComplete} 
                className="btn-primary"
                disabled={loading || isUnderage}
              >
                {loading ? "Processing..." : isUnderage ? "Action Disabled (Under 18)" : "Mark Done & Continue"}
              </button>
            </div>
          </>
        )}

        {/* Quick Actions */}
        <div style={{ marginBottom: '1rem', fontSize: '0.9rem', color: '#64748b' }}>
          Need specific help?
        </div>
        <div className="quick-actions">
          <button className="btn-secondary" onClick={() => fetchStep("I moved recently")}>
            I moved recently
          </button>
          <button className="btn-secondary" onClick={() => fetchStep("I missed deadline")}>
            I missed deadline
          </button>
          <button className="btn-secondary" onClick={() => fetchStep("My name isn't on list")}>
            My name isn't on list
          </button>
          <button className="btn-secondary" onClick={() => navigate('/timeline')}>
            View Full Timeline
          </button>
        </div>

        {/* Micro Feedback Toast */}
        {showToast && (
          <div className="feedback-toast">
            ✔ Step completed
          </div>
        )}

      </div>
    </div>
  );
};

export default Journey;
