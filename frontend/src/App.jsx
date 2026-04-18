import { useState } from 'react';
import './index.css';

function App() {
  const [topic, setTopic] = useState('');
  const [theme, setTheme] = useState('dark');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');

  const generatePresentation = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setIsGenerating(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8001/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic, theme }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate presentation');
      }

      // Download file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${topic.replace(/\s+/g, '_')}.pptx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

    } catch (err) {
      setError(err.message || 'An error occurred during generation.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="app-container">
      <div className="background-effect"></div>
      
      <main className="main-content">
        <header className="hero-section">
          <div className="badge">AI Powered</div>
          <h1 className="title">
            Magic <span className="highlight">Presentations</span>
          </h1>
          <p className="subtitle">
            Instantly generate a beautiful, fully-structured PowerPoint on any topic simply by describing it.
          </p>
        </header>

        <form className="generator-form" onSubmit={generatePresentation}>
          <div className="input-group">
            <input
              type="text"
              className="topic-input"
              placeholder="e.g., The Future of Quantum Computing, How to Start a Garden..."
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              disabled={isGenerating}
              required
            />
            <select 
              className="theme-select" 
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
              disabled={isGenerating}
            >
              <option value="dark">Dark Theme</option>
              <option value="light">Light Theme</option>
              <option value="blue">Blue Theme</option>
            </select>
            <button 
              type="submit" 
              className={`generate-btn ${isGenerating ? 'generating' : ''}`}
              disabled={isGenerating || !topic.trim()}
            >
              {isGenerating ? (
                <>
                  <span className="spinner"></span>
                  Building Slides...
                </>
              ) : (
                'Generate Magic ✨'
              )}
            </button>
          </div>
          {error && <p className="error-message">{error}</p>}
        </form>

        <div className="features-grid">
          <div className="feature-card">
            <div className="icon">🚀</div>
            <h3>Instant Generation</h3>
            <p>From zero to full presentation in seconds. Your thoughts, materialized instantly.</p>
          </div>
          <div className="feature-card">
            <div className="icon">🧠</div>
            <h3>Smart Structuring</h3>
            <p>AI organizes your topic logically with dynamic layout formatting.</p>
          </div>
          <div className="feature-card">
            <div className="icon">🖼️</div>
            <h3>Auto Images</h3>
            <p>Automatically fetches and embeds highly relevant images magically.</p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
