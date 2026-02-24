import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import './RootLayout.css'

interface RootLayoutProps {
  children: ReactNode
}

export function RootLayout({ children }: RootLayoutProps) {
  const location = useLocation()
  const isSettings = location.pathname === '/settings'

  return (
    <div className="app-root">
      <header className="topbar">
        <Link to="/" className="topbar-brand">
          SHERLOCK HOMES
        </Link>
        <nav className="topbar-nav">
          {isSettings ? (
            <Link to="/" className="topbar-link">
              &larr; Back
            </Link>
          ) : (
            <Link to="/settings" className="topbar-link">
              Settings
            </Link>
          )}
        </nav>
      </header>
      <div className="app-body">{children}</div>
    </div>
  )
}
