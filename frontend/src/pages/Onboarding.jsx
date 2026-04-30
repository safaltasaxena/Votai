import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

const REGIONS = [
  { name: "Maharashtra", id: "IN-MH" },
  { name: "Delhi", id: "IN-DL" },
  { name: "Karnataka", id: "IN-KA" },
  { name: "Uttar Pradesh", id: "IN-UP" },
  { name: "Tamil Nadu", id: "IN-TN" }
];

const Onboarding = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null); // Added
  const [formData, setFormData] = useState({
    age: '',
    country: 'India',
    region_id: 'IN-MH',
    language: 'en',
    isFirstTimeVoter: true
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.age || !formData.region_id) {
      setError("Please fill in all required fields.");
      return;
    }

    setLoading(true);
    try {
      const userId = `user_${Math.random().toString(36).substr(2, 9)}`;
      const selectedRegion = REGIONS.find(r => r.id === formData.region_id);
      
      const payload = {
        user_id: userId,
        age: parseInt(formData.age),
        country: formData.country,
        state: selectedRegion.name,
        language: formData.language,
        first_time_voter: formData.isFirstTimeVoter
      };

      await api.createUser(payload);

      // Persist user details
      localStorage.setItem('votai_user_id', userId);
      localStorage.setItem('votai_user_age', formData.age); // Added
      localStorage.setItem('votai_region_id', selectedRegion.id);
      localStorage.setItem('votai_region_name', selectedRegion.name);
      
      navigate('/journey');
    } catch (err) {
      console.error("Onboarding failed:", err);
      setError(err.message || "Failed to start journey. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="onboarding-card">
        <h1>Welcome to Votai</h1>
        <p style={{ color: '#94a3b8', marginBottom: '2rem' }}>
          Let's get you ready for the election. Fill in your details to start.
        </p>

        {error && (
          <div style={{ color: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', padding: '0.75rem', borderRadius: '6px', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="age">Age</label>
            <input
              type="number"
              id="age"
              name="age"
              value={formData.age}
              onChange={handleChange}
              placeholder="Enter your age"
              required
              min="1"
            />
          </div>

          <div className="form-group">
            <label htmlFor="country">Country</label>
            <select
              id="country"
              name="country"
              value={formData.country}
              onChange={handleChange}
            >
              <option value="India">India</option>
              <option value="USA">USA</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="region_id">State / Region</label>
            <select
              id="region_id"
              name="region_id"
              value={formData.region_id}
              onChange={handleChange}
              required
            >
              {REGIONS.map(reg => (
                <option key={reg.id} value={reg.id}>{reg.name}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="language">Preferred Language</label>
            <select
              id="language"
              name="language"
              value={formData.language}
              onChange={handleChange}
            >
              <option value="en">English</option>
              <option value="hi">Hindi</option>
              <option value="mr">Marathi</option>
            </select>
          </div>

          <div className="form-group">
            <label className="checkbox-group">
              <input
                type="checkbox"
                name="isFirstTimeVoter"
                checked={formData.isFirstTimeVoter}
                onChange={handleChange}
              />
              <span>I am a first-time voter</span>
            </label>
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Starting..." : "Start Journey"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Onboarding;
