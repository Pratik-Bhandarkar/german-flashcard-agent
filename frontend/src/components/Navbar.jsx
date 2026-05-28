import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

function Navbar() {
  const [isDark, setIsDark] = useState(() => localStorage.getItem('theme') === 'dark')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
    localStorage.setItem('theme', isDark ? 'dark' : 'light')
  }, [isDark])

  return (
    <nav className="bg-blue-600 dark:bg-gray-800 text-white px-6 py-4 shadow-sm">
      <div className="max-w-4xl mx-auto flex justify-between items-center">
        <h1 className="text-xl font-bold">🇩🇪 Flashcard Agent</h1>
        <div className="flex gap-6 items-center">
          <Link to="/" className="hover:text-blue-200 dark:hover:text-gray-300">Home</Link>
          <Link to="/study" className="hover:text-blue-200 dark:hover:text-gray-300">Study</Link>
          <Link to="/add" className="hover:text-blue-200 dark:hover:text-gray-300">Add Vocab</Link>
          <Link to="/translate" className="hover:text-blue-200 dark:hover:text-gray-300">Translate</Link>
          <Link to="/library" className="hover:text-blue-200 dark:hover:text-gray-300">Library</Link>
          <button
            onClick={() => setIsDark(!isDark)}
            className="text-lg hover:opacity-80 transition-opacity"
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDark ? '☀️' : '🌙'}
          </button>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
