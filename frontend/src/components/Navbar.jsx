import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'

function Navbar() {
  const [isDark, setIsDark] = useState(() => localStorage.getItem('theme') === 'dark')
  const location = useLocation()

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
    localStorage.setItem('theme', isDark ? 'dark' : 'light')
  }, [isDark])

  const isActive = (path) =>
    path === '/' ? location.pathname === '/' : location.pathname.startsWith(path)

  const navLink = (to, label) => (
    <Link
      to={to}
      className={`text-sm font-medium transition-colors px-3 py-1.5 rounded-lg
        ${isActive(to)
          ? 'bg-white/20 text-white'
          : 'text-blue-100/80 hover:text-white hover:bg-white/10'
        }`}
    >
      {label}
    </Link>
  )

  return (
    <nav className="bg-gradient-to-r from-blue-700 to-blue-600
                    dark:from-gray-900 dark:to-gray-800
                    border-b border-blue-500/30 dark:border-gray-700
                    text-white px-6 py-3 shadow-md">
      <div className="max-w-4xl mx-auto flex justify-between items-center">
        <Link to="/" className="flex items-center gap-2 font-bold text-lg tracking-tight hover:opacity-90 transition-opacity">
          <span>⚡</span>
          <span>Wortblitz</span>
        </Link>
        <div className="flex gap-1 items-center">
          {navLink('/', 'Home')}
          {navLink('/study', 'Study')}
          {navLink('/add', 'Add Vocab')}
          {navLink('/translate', 'Translate')}
          {navLink('/library', 'Library')}
          <button
            onClick={() => setIsDark(!isDark)}
            className="ml-2 text-lg hover:opacity-80 transition-opacity p-1.5 rounded-lg hover:bg-white/10"
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
