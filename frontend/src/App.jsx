// App.jsx
// Root component — sets up navigation between all three pages.
// BrowserRouter enables URL-based navigation.
// Each Route maps a URL path to a page component.

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Study from './pages/Study'
import Add from './pages/Add'
import Translate from './pages/Translate'
import Navbar from './components/Navbar'

function App() {
  return (
    <BrowserRouter>
      {/* Navbar appears on every page */}
      <Navbar />

      {/* Main content area */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/study" element={<Study />} />
          <Route path="/add" element={<Add />} />
          <Route path="/translate" element={<Translate />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}

export default App