import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

const PartyCard = ({ party }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="party-card">
      <div className="party-header">
        <h3>{party.name}</h3>
        <button className="expand-link" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Show less" : "View details"}
        </button>
      </div>

      <div className="tag-container">
        {(party.focus_areas || []).map((area, index) => (
          <span key={index} className="tag">{area}</span>
        ))}
      </div>

      {expanded && (
        <div className="policy-details">
          <h4>Key Policies:</h4>
          <ul style={{ paddingLeft: '1.2rem', marginTop: '0.5rem' }}>
            {(party.key_policies || []).map((policy, index) => (
              <li key={index} style={{ marginBottom: '0.4rem' }}>{policy}</li>
            ))}
          </ul>
          {party.past_work && party.past_work.length > 0 && (
            <>
              <h4 style={{ marginTop: '1rem' }}>Past Work:</h4>
              <ul style={{ paddingLeft: '1.2rem', marginTop: '0.5rem' }}>
                {party.past_work.map((work, index) => (
                  <li key={index} style={{ marginBottom: '0.4rem' }}>{work}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
};

const PartyExplorer = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [parties, setParties] = useState([]);
  const [disclaimer, setDisclaimer] = useState('');
  const regionId = localStorage.getItem('votai_region_id') || 'IN-MH';

  useEffect(() => {
    const fetchParties = async () => {
      try {
        setLoading(true);
        const data = await api.getParties(regionId);
        setParties(data.parties);
        setDisclaimer(data.disclaimer);
      } catch (err) {
        console.error("Parties fetch failed:", err);
        setError("Could not load party information.");
      } finally {
        setLoading(false);
      }
    };
    fetchParties();
  }, [regionId]);

  if (loading) return <div className="page"><p>Loading parties...</p></div>;
  if (error) return <div className="page"><p style={{ color: '#ef4444' }}>{error}</p></div>;

  if (!parties || parties.length === 0) return (
    <div className="page">
      <h1>Explore Parties</h1>

      <div className="disclaimer-banner">
        {disclaimer || "This information is provided for awareness only and does not recommend or endorse any candidate or party."}
      </div>

      <p style={{ color: '#94a3b8', marginTop: '2rem' }}>
        No party data available for this region yet.
      </p>
    </div>
  );

  return (
    <div className="page">
      <h1>Explore Parties</h1>

      {/* Mandatory Disclaimer */}
      <div className="disclaimer-banner">
        {disclaimer || "This information is provided for awareness only and does not recommend or endorse any candidate or party."}
      </div>

      <div className="party-list">
        {parties.map((party, index) => (
          <PartyCard key={index} party={party} />
        ))}
      </div>
    </div>
  );
};

export default PartyExplorer;
