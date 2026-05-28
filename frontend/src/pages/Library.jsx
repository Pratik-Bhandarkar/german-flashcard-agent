import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getLibraryLevels } from '../services/api'

const LEVEL_STYLES = {
  A1: { badge: 'bg-green-900/40 text-green-300',   bar: 'bg-green-500',   topBorder: 'border-t-green-500',   glow: 'hover:shadow-green-900/30' },
  A2: { badge: 'bg-emerald-900/40 text-emerald-300', bar: 'bg-emerald-500', topBorder: 'border-t-emerald-500', glow: 'hover:shadow-emerald-900/30' },
  B1: { badge: 'bg-blue-900/40 text-blue-300',     bar: 'bg-blue-500',    topBorder: 'border-t-blue-500',    glow: 'hover:shadow-blue-900/30' },
  B2: { badge: 'bg-violet-900/40 text-violet-300', bar: 'bg-violet-500',  topBorder: 'border-t-violet-500',  glow: 'hover:shadow-violet-900/30' },
  C1: { badge: 'bg-amber-900/40 text-amber-300',   bar: 'bg-amber-500',   topBorder: 'border-t-amber-500',   glow: 'hover:shadow-amber-900/30' },
  C2: { badge: 'bg-rose-900/40 text-rose-300',     bar: 'bg-rose-500',    topBorder: 'border-t-rose-500',    glow: 'hover:shadow-rose-900/30' },
}

function LevelCard({ level }) {
  const styles = LEVEL_STYLES[level.level] || LEVEL_STYLES.B1
  const pct = level.total_words > 0
    ? Math.round((level.activated_words / level.total_words) * 100)
    : 0

  return (
    <div className={`border-t-4 ${styles.topBorder} rounded-xl p-5 transition-all duration-200
                     dark:bg-gray-800/60 border dark:border-gray-700/60
                     hover:shadow-lg hover:-translate-y-0.5 ${styles.glow}
                     ${level.locked ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}>
      <div className="flex justify-between items-start mb-3">
        <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${styles.badge}`}>
          {level.level}
        </span>
        {level.locked && <span className="text-base leading-none">🔒</span>}
      </div>

      <h3 className="font-semibold text-gray-100 mb-1">{level.label}</h3>

      {level.locked ? (
        <p className="text-xs text-gray-500 mt-2">Coming soon</p>
      ) : (
        <>
          <p className="text-xs text-gray-400 mb-2">
            {level.activated_words} / {level.total_words} words added
          </p>
          <div className="w-full bg-gray-700 rounded-full h-1.5 mb-4">
            <div
              className={`${styles.bar} h-1.5 rounded-full transition-all duration-500`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <Link
            to={`/library/${level.level.toLowerCase()}`}
            className="text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
          >
            Browse →
          </Link>
        </>
      )}
    </div>
  )
}

function Library() {
  const [levels, setLevels] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getLibraryLevels()
      .then(r => setLevels(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="text-center text-gray-500 mt-20">Loading library…</div>
  )

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold dark:text-white">Vocabulary Library</h2>
        <p className="text-gray-400 text-sm mt-1">
          Browse pre-enriched word lists and add them to your study deck.
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {levels.map(level => (
          <LevelCard key={level.level} level={level} />
        ))}
      </div>
    </div>
  )
}

export default Library
