import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Onboarding from './pages/Onboarding';
import Journey from './pages/Journey';
import Timeline from './pages/Timeline';
import PartyExplorer from './pages/PartyExplorer';

// Placeholder Components
const TopNav = () => (
  <header className="top-nav">
    <div className="logo">Votai</div>
    <nav>
      <Link to="/">Onboarding</Link>
      <Link to="/journey">Journey</Link>
      <Link to="/timeline">Timeline</Link>
      <Link to="/parties">Parties</Link>
    </nav>
  </header>
);

const Ready = () => <div className="page"><h1>Ready to Vote</h1><p>You have completed your journey!</p></div>;

function App() {
  return (
    <Router>
      <div className="app-container">
        <TopNav />
        <main className="content">
          <Routes>
            <Route path="/" element={<Onboarding />} />
            <Route path="/journey" element={<Journey />} />
            <Route path="/timeline" element={<Timeline />} />
            <Route path="/parties" element={<PartyExplorer />} />
            <Route path="/ready" element={<Ready />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
