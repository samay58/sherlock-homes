import { Link } from 'react-router-dom'
import './HomePage.css'

export function HomePage() {
  return (
    <div className="home">
      <div className="home-content">
        <h1 className="home-title">Sherlock Homes</h1>

        <p className="home-tagline">
          What's worth your time,<br />
          not just what's for sale.
        </p>

        <p className="home-description">
          Every listing scored for light, quiet, and pricing shifts.
        </p>

        <div className="home-cta">
          <span className="home-cta-label">Case Files</span>
          <Link to="/matches" className="home-cta-primary">
            View my matches <span className="home-cta-arrow" aria-hidden="true">&rarr;</span>
          </Link>
          <span className="home-cta-alt">
            or <Link to="/criteria" className="home-cta-secondary">set your criteria</Link>
          </span>
        </div>

        <footer className="home-signals">
          <span className="home-signals-label">Signals We Track</span>
          <span className="home-signals-list">
            Light <span className="home-dot" aria-hidden="true"></span>{' '}
            Quiet <span className="home-dot" aria-hidden="true"></span>{' '}
            Value
          </span>
        </footer>
      </div>
    </div>
  )
}
