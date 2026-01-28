import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Agentation } from 'agentation'
import { RootLayout } from './components/layout/RootLayout'
import { HomePage } from './pages/HomePage'
import { MatchesPage } from './pages/MatchesPage'
import { ListingsPage } from './pages/ListingsPage'
import { ListingDetailPage } from './pages/ListingDetailPage'
import { CriteriaPage } from './pages/CriteriaPage'

function App() {
  return (
    <BrowserRouter>
      <RootLayout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/matches" element={<MatchesPage />} />
          <Route path="/listings" element={<ListingsPage />} />
          <Route path="/listings/:id" element={<ListingDetailPage />} />
          <Route path="/criteria" element={<CriteriaPage />} />
        </Routes>
      </RootLayout>
      {import.meta.env.DEV && <Agentation />}
    </BrowserRouter>
  )
}

export default App
