import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

const Timeline = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const regionId = localStorage.getItem('votai_region_id') || 'IN-MH';

  useEffect(() => {
    const fetchTimeline = async () => {
      try {
        setLoading(true);
        const data = await api.getTimeline(regionId);
        setTimeline(data.timeline);
      } catch (err) {
        console.error("Timeline fetch failed:", err);
        setError("Connecting to civic system...");
      } finally {
        setLoading(false);
      }
    };
    fetchTimeline();
  }, [regionId]);

  if (loading) return <div className="page"><p>Loading timeline...</p></div>;

  if (error) return (
    <div className="page" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
      <p style={{ color: '#ef4444', marginBottom: '1.5rem' }}>{error}</p>
      <button onClick={() => window.location.reload()} className="btn-secondary">Retry</button>
    </div>
  );

  if (!timeline || !timeline.election_date) return (
    <div className="page">
      <h1>Election Timeline</h1>
      <p style={{ color: '#94a3b8', marginTop: '2rem' }}>
        No election data available for this region yet. Please check back later.
      </p>
      <button onClick={() => navigate('/')} className="btn-secondary" style={{ marginTop: '1rem' }}>
        Change Region
      </button>
    </div>
  );

  const events = [
    { label: "Registration Deadline", date: timeline.registration_deadline, urgent: true },
    { label: "Verification Deadline", date: timeline.verification_deadline },
    { label: "Election Day", date: timeline.election_date }
  ];

  return (
    <div className="page">
      <h1>Election Timeline</h1>
      <p style={{ color: '#94a3b8', marginBottom: '2rem' }}>
        Keep track of these important dates for the Maharashtra State Elections.
      </p>

      {/* Alert */}
      <div className="alert-deadline">
        <span>⚠️</span>
        <span><strong>Deadline approaching:</strong> You have 12 days left to register.</span>
      </div>

      <div className="timeline-list">
        {events.map((item, index) => (
          <div
            key={index}
            className="timeline-item"
            style={item.urgent ? { borderColor: '#eab308' } : {}}
          >
            <span className="timeline-label">
              {item.label}
              {item.urgent && <span style={{ color: '#eab308', marginLeft: '0.5rem', fontSize: '0.8rem' }}>(Urgent)</span>}
            </span>
            <span className="timeline-date">{item.date}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Timeline;
