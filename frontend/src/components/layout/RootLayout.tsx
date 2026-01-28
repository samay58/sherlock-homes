import { useEffect, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import './RootLayout.css'

interface RootLayoutProps {
  children: ReactNode
}

export function RootLayout({ children }: RootLayoutProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <div className="app-container">
      <header className="sherlock-header">
        <nav>
          <Link to="/" className="brand">
            <span className="brand-icon">&#128269;</span>
            <span className="brand-name">Sherlock Homes</span>
          </Link>
          <ul className="nav-menu">
            <li><Link to="/listings" className="nav-link">Browse</Link></li>
            <li><Link to="/matches" className="nav-link">Matches</Link></li>
            <li><Link to="/criteria" className="nav-link">Criteria</Link></li>
          </ul>
        </nav>
      </header>

      <main className={mounted ? 'mounted' : ''}>
        {children}
      </main>

      <footer className="sherlock-footer">
        <span className="footer-brand">Sherlock Homes</span>
        <span className="footer-divider">|</span>
        <span className="footer-tagline">Insight over inventory</span>
      </footer>
    </div>
  )
}
