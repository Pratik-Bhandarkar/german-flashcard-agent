// Navbar.jsx
// Navigation bar shown on every page.
// Link components handle navigation without full page reloads.

import { Link } from 'react-router-dom'

function Navbar() {
  return (
    <nav className="bg-blue-600 text-white px-6 py-4">
      <div className="max-w-4xl mx-auto flex justify-between items-center">
        <h1 className="text-xl font-bold">🇩🇪 Flashcard Agent</h1>
        <div className="flex gap-6">
          <Link to="/" className="hover:text-blue-200">Home</Link>
          <Link to="/study" className="hover:text-blue-200">Study</Link>
          <Link to="/add" className="hover:text-blue-200">Add Vocab</Link>
        </div>
      </div>
    </nav>
  )
}

export default Navbar