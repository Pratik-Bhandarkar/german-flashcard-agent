import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getLibraryLevels } from '../services/api'

const LEVEL_STYLES = {
  A1: { badge: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300',   bar: 'bg-green-500',  card: 'border-green-200 dark:border-green-700/50 hover:border-green-300 dark:hover:border-green-600' },
  A2: { badge: 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300', bar: 'bg-emerald-500', card: 'border-emerald-200 dark:border-emerald-700/50 hover:border-emerald-300 dark:hover:border-emerald-600' },
  B1: { badge: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',       bar: 'bg-blue-500',   card: 'border-blue-200 dark:border-blue-700/50 hover:border-blue-400 dark:hover:border-blue-500' },
  B2: { badge: 'bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300', bar: 'bg-violet-500', card: 'border-violet-200 dark:border-violet-700/50 hover:border-violet-300 dark:hover:border-violet-600' },
  C1: { badge: 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300',   bar: 'bg-amber-500',  card: 'border-amber-200 dark:border-amber-700/50 hover:border-amber-300 dark:hover:border-amber-600' },
  C2: { badge: 'bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300',       bar: 'bg-rose-500',   card: 'border-rose-200 dark:border-rose-700/50 hover:border-rose-300 dark:hover:border-rose-600' },
}

function LevelCard({ level }) {
  const styles = LEVEL_STYLES[level.level] || LEVEL_STYLES.B1
  const pct = level.total_words > 0
    ? Math.round((level.activated_words / level.total_words) * 100)
    : 0

  return (
    <div className={`border-2 rounded-xl p-5 transition-colors dark:bg-gray-800/50
                     ${styles.card} ${level.locked ? 'opacity-55 cursor-not-allowed' : ''}`}>
      <div className="flex justify-between items-start mb-3">
        <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${styles.badge}`}>
          {level.level}
        </span>
        {level.locked && <span className="text-lg leading-none">🔒</span>}
      </div>

      <h3 className="font-semibold text-gray-800 dark:text-gray-100 mb-1">{level.label}</h3>

      {level.locked ? (
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">Coming soon</p>
      ) : (
        <>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
            {level.activated_words} / {level.total_words} words added
          </p>
          <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5 mb-4">
            <div
              className={`${styles.bar} h-1.5 rounded-full transition-all duration-500`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <Link
            to={`/library/${level.level.toLowerCase()}`}
            className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline"
          >
            Browse &rarr;
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
    <div className="text-center text-gray-500 dark:text-gray-400 mt-20">Loading library...</div>
  )

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold dark:text-white">Vocabulary Library</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
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
