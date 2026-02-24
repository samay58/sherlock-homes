import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Agentation } from 'agentation'
import { RootLayout } from './components/layout/RootLayout'
import { WorkspaceView } from './components/workspace/WorkspaceView'
import { CriteriaPage } from './pages/CriteriaPage'

function App() {
  return (
    <BrowserRouter>
      <RootLayout>
        <Routes>
          <Route path="/" element={<WorkspaceView />} />
          <Route path="/settings" element={<CriteriaPage />} />
        </Routes>
      </RootLayout>
      {import.meta.env.DEV && <Agentation />}
    </BrowserRouter>
  )
}

export default App
