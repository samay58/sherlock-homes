import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import './HomePage.css'

export function HomePage() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <main className={`hero-container ${mounted ? 'mounted' : ''}`}>
      <div className="hero-content">
        <div className="hero-icon" aria-hidden="true">&#128269;</div>

        <h1 className="hero-title">Sherlock Homes</h1>

        <p className="hero-tagline">Insight over inventory.</p>

        <p className="hero-description">
          Zillow shows you what's for sale. We show you what's worth your time. AI-powered matching
          that understands light, quiet, and vibe.
        </p>

        <div className="hero-stats">
          <div className="stat">
            <span className="stat-value">3</span>
            <span className="stat-label">Vibe Presets</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat">
            <span className="stat-value">100+</span>
            <span className="stat-label">Signals Analyzed</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat">
            <span className="stat-value">SF</span>
            <span className="stat-label">Bay Area Focus</span>
          </div>
        </div>

        <div className="hero-actions">
          <Link to="/matches" className="btn-primary">
            View My Matches
            <span className="btn-arrow" aria-hidden="true">&#8594;</span>
          </Link>
          <Link to="/criteria" className="btn-secondary">
            Set Criteria
          </Link>
        </div>

        <div className="hero-features">
          <div className="feature">
            <span className="feature-icon" role="img" aria-label="Sun">&#9728;</span>
            <span className="feature-name">Light Potential</span>
            <span className="feature-desc">NLP + heuristics</span>
          </div>
          <div className="feature">
            <span className="feature-icon" role="img" aria-label="Sound waves">&#128263;</span>
            <span className="feature-name">Tranquility Score</span>
            <span className="feature-desc">Geospatial analysis</span>
          </div>
          <div className="feature">
            <span className="feature-icon" role="img" aria-label="Chart">&#128200;</span>
            <span className="feature-name">Deal Detection</span>
            <span className="feature-desc">Price drop tracking</span>
          </div>
        </div>
      </div>
    </main>
  )
}
