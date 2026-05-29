import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getFlashcardStats, getLibraryLevels, getWordsOfDay, activateWord } from '../services/api'
import { speak } from '../utils/speech'

const WC_COLORS = {
  noun: 'text-blue-400',
  verb: 'text-green-400',
  adjective: 'text-amber-400',
  adverb: 'text-purple-400',
}

function WordCard({ word, onAdd }) {
  const [flipped, setFlipped] = useState(false)
  const [added, setAdded] = useState(false)
  const [adding, setAdding] = useState(false)

  const handleAdd = async (e) => {
    e.stopPropagation()
    setAdding(true)
    try {
      await onAdd(word)
      setAdded(true)
    } catch (err) {
      if (err.response?.status === 409) setAdded(true)
    } finally {
      setAdding(false)
    }
  }

  return (
    <div className="wotd-container" onClick={() => setFlipped(f => !f)}>
      <div className={`wotd-inner ${flipped ? 'is-flipped' : ''}`}>
        {/* Front */}
        <div className="wotd-face rounded-xl border dark:border-gray-700 dark:bg-gray-800/80
                        bg-white flex flex-col justify-between p-4 shadow-sm
                        hover:border-blue-500/50 transition-colors">
          <div>
            {word.word_class && (
              <span className={`text-xs uppercase tracking-wider font-semibold ${WC_COLORS[word.word_class] || 'text-gray-400'}`}>
                {word.word_class}
              </span>
            )}
            <h3 className="text-xl font-bold text-blue-400 mt-1 leading-tight">
              {word.gender && <span className="text-gray-400 font-normal text-sm">{word.gender} </span>}
              {word.german_word}
            </h3>
            {word.plural_form && (
              <p className="text-gray-500 text-xs mt-0.5">({word.plural_form})</p>
            )}
          </div>
          <div className="flex items-center justify-center gap-3 mt-3">
            <p className="text-gray-500 text-xs">tap to reveal</p>
            <button
              onClick={(e) => { e.stopPropagation(); speak(word.gender ? `${word.gender} ${word.german_word}` : word.german_word) }}
              className="text-gray-500 hover:text-blue-400 transition-colors text-base leading-none"
              title="Pronounce"
            >
              🔊
            </button>
          </div>
        </div>

        {/* Back */}
        <div className="wotd-face wotd-back rounded-xl border dark:border-gray-700 dark:bg-gray-800/80
                        bg-white flex flex-col justify-between p-4 shadow-sm">
          <div>
            <p className="text-xs text-gray-500 mb-1 font-medium">{word.german_word}</p>
            <p className="text-lg font-bold text-green-400 leading-tight">{word.english_translation}</p>
            <p className="text-gray-400 text-sm italic mt-3 leading-relaxed">
              {word.example_sentence_de}
            </p>
            {word.example_sentence_en && (
              <p className="text-gray-500 text-sm mt-1 leading-relaxed">
                {word.example_sentence_en}
              </p>
            )}
            {word.mnemonic && (
              <p className="text-yellow-500/80 text-sm mt-2">💡 {word.mnemonic}</p>
            )}
          </div>
          <button
            onClick={handleAdd}
            disabled={added || adding}
            className={`mt-3 text-xs font-medium px-3 py-1.5 rounded-lg transition-all
              ${added
                ? 'bg-green-900/30 text-green-400 cursor-default'
                : 'bg-blue-600/20 text-blue-400 hover:bg-blue-600/40 active:scale-95'
              }`}
          >
            {added ? '✓ Added to deck' : adding ? '…' : '+ Add to deck'}
          </button>
        </div>
      </div>
    </div>
  )
}

function StatBox({ value, label, color }) {
  return (
    <div className="bg-gray-800/60 rounded-xl p-4 text-center">
      <div className={`text-3xl font-bold ${color}`}>{value ?? '—'}</div>
      <div className="text-xs text-gray-400 mt-1">{label}</div>
    </div>
  )
}

function Home() {
  const [stats, setStats] = useState(null)
  const [libraryLevels, setLibraryLevels] = useState([])
  const [wordsOfDay, setWordsOfDay] = useState([])

  useEffect(() => {
    getFlashcardStats().then(r => setStats(r.data)).catch(() => {})
    getLibraryLevels().then(r => setLibraryLevels(r.data)).catch(() => {})
    getWordsOfDay().then(r => setWordsOfDay(r.data)).catch(() => {})
  }, [])

  const handleAddWord = (word) => activateWord('b1', word.id)
  const activeLibraryLevels = libraryLevels.filter(l => !l.locked && l.total_words > 0)
  const hasSession = stats && (stats.due_today > 0 || stats.new_cards > 0)
  const sessionSize = stats ? Math.min((stats.due_today || 0) + (stats.new_cards || 0), 20) : 0

  return (
    <div className="space-y-8">

      {/* Hero */}
      <div className="rounded-2xl bg-gradient-to-br from-blue-900/50 via-gray-800/60 to-gray-900/80
                      border dark:border-gray-700/60 p-6 md:p-8">
        <h2 className="text-3xl font-bold text-white mb-1">Guten Tag! 👋</h2>
        <p className="text-gray-400 text-sm">Your German vocabulary coach is ready.</p>

        <div className="grid grid-cols-4 gap-3 mt-6">
          <StatBox
            value={stats ? `${stats.streak}🔥` : null}
            label="Day streak"
            color="text-orange-400"
          />
          <StatBox
            value={stats?.due_today ?? '—'}
            label="To review"
            color="text-blue-400"
          />
          <StatBox
            value={stats?.new_cards ?? '—'}
            label="New"
            color="text-purple-400"
          />
          <StatBox
            value={stats?.total}
            label="Total cards"
            color="text-green-400"
          />
        </div>

        <div className="flex gap-3 mt-5 flex-wrap">
          <Link
            to="/study"
            className={`px-5 py-2.5 rounded-xl font-medium transition-all active:scale-95
              ${hasSession
                ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/40'
                : 'bg-gray-700 hover:bg-gray-600 text-white'
              }`}
          >
            {hasSession ? `Study Now (${sessionSize})` : 'Nothing due'}
          </Link>
          <Link to="/library"
            className="bg-gray-700/60 hover:bg-gray-700 text-gray-200 px-5 py-2.5 rounded-xl
                       font-medium transition-all border dark:border-gray-600 active:scale-95">
            Browse Library
          </Link>
          <Link to="/add"
            className="bg-gray-700/60 hover:bg-gray-700 text-gray-200 px-5 py-2.5 rounded-xl
                       font-medium transition-all border dark:border-gray-600 active:scale-95">
            + Add Vocab
          </Link>
        </div>
      </div>

      {/* Words of the Day */}
      {wordsOfDay.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-100">Words of the Day</h3>
            <span className="text-xs text-gray-500">
              {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
            </span>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {wordsOfDay.map(word => (
              <WordCard key={word.id} word={word} onAdd={handleAddWord} />
            ))}
          </div>
        </div>
      )}

      {/* Library progress */}
      {activeLibraryLevels.length > 0 && (
        <div className="border dark:border-gray-700 rounded-xl p-4 dark:bg-gray-800/40">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold text-gray-100">Vocabulary Library</h3>
            <Link to="/library" className="text-sm text-blue-400 hover:underline">Browse →</Link>
          </div>
          {activeLibraryLevels.map(l => {
            const pct = l.total_words > 0 ? Math.round((l.activated_words / l.total_words) * 100) : 0
            return (
              <div key={l.level} className="mb-2 last:mb-0">
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>{l.level} — {l.label}</span>
                  <span>{l.activated_words} / {l.total_words} words</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-1.5">
                  <div className="bg-blue-500 h-1.5 rounded-full transition-all duration-500"
                       style={{ width: `${pct}%` }} />
                </div>
              </div>
            )
          })}
        </div>
      )}

    </div>
  )
}

export default Home
