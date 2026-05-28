import { useEffect, useState } from 'react'
import { getReviewCards, getAllFlashcards, updateFlashcard } from '../services/api'
import { speak } from '../utils/speech'

const WC_COLORS = {
  noun: 'text-blue-400 bg-blue-900/30',
  verb: 'text-green-400 bg-green-900/30',
  adjective: 'text-amber-400 bg-amber-900/30',
  adverb: 'text-purple-400 bg-purple-900/30',
}

const getNextReviewDate = (difficulty) => {
  const today = new Date()
  const days = { easy: 7, medium: 3, hard: 1 }
  today.setDate(today.getDate() + days[difficulty])
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function Study() {
  const [cards, setCards] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)
  const [loading, setLoading] = useState(true)
  const [finished, setFinished] = useState(false)
  const [results, setResults] = useState({ easy: 0, medium: 0, hard: 0 })

  useEffect(() => { fetchCards() }, [])

  const fetchCards = async () => {
    setLoading(true)
    try {
      const response = await getReviewCards()
      setCards(response.data)
    } catch (error) {
      console.error('Failed to fetch cards:', error)
    } finally {
      setLoading(false)
    }
  }

  const resetSession = (newCards) => {
    setCurrentIndex(0)
    setIsFlipped(false)
    setFinished(false)
    setResults({ easy: 0, medium: 0, hard: 0 })
    if (newCards) setCards(newCards)
  }

  const handleRate = async (difficulty) => {
    const card = cards[currentIndex]
    try {
      await updateFlashcard(card.id, {
        difficulty,
        next_review: getNextReviewDate(difficulty)
      })
      setResults(prev => ({ ...prev, [difficulty]: prev[difficulty] + 1 }))
      if (currentIndex + 1 >= cards.length) {
        setFinished(true)
      } else {
        setCurrentIndex(currentIndex + 1)
        setIsFlipped(false)
      }
    } catch (error) {
      console.error('Failed to update card:', error)
    }
  }

  if (loading) return (
    <div className="text-center text-gray-500 dark:text-gray-400 mt-20">Loading cards…</div>
  )

  if (cards.length === 0) return (
    <div className="text-center mt-20">
      <div className="text-5xl mb-4">📚</div>
      <p className="text-gray-400 mb-6">No cards due for review today.</p>
      <button
        onClick={async () => {
          setLoading(true)
          try {
            const response = await getAllFlashcards()
            resetSession(response.data)
          } catch (error) {
            console.error('Failed to fetch all cards:', error)
          } finally {
            setLoading(false)
          }
        }}
        className="bg-blue-600 text-white px-6 py-2.5 rounded-xl hover:bg-blue-500 font-medium transition-colors"
      >
        Practice All Cards
      </button>
    </div>
  )

  if (finished) return (
    <div className="text-center mt-16 max-w-sm mx-auto">
      <div className="text-6xl mb-4">🎉</div>
      <h2 className="text-2xl font-bold mb-1 dark:text-white">Session Complete!</h2>
      <p className="text-gray-400 text-sm mb-8">You reviewed {cards.length} cards</p>

      <div className="grid grid-cols-3 gap-3 mb-8">
        <div className="bg-red-900/30 border border-red-800/40 rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-red-400">{results.hard}</div>
          <div className="text-xs text-gray-400 mt-1">Hard</div>
        </div>
        <div className="bg-yellow-900/30 border border-yellow-800/40 rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-yellow-400">{results.medium}</div>
          <div className="text-xs text-gray-400 mt-1">Medium</div>
        </div>
        <div className="bg-green-900/30 border border-green-800/40 rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-green-400">{results.easy}</div>
          <div className="text-xs text-gray-400 mt-1">Easy</div>
        </div>
      </div>

      <div className="flex gap-3 justify-center">
        <button
          onClick={() => resetSession()}
          className="bg-blue-600 text-white px-6 py-2.5 rounded-xl hover:bg-blue-500 font-medium transition-colors"
        >
          Study Again
        </button>
        <button
          onClick={() => { resetSession(); fetchCards() }}
          className="bg-gray-700 text-gray-300 px-6 py-2.5 rounded-xl hover:bg-gray-600 font-medium transition-colors"
        >
          New Session
        </button>
      </div>
    </div>
  )

  const card = cards[currentIndex]
  const wcStyle = WC_COLORS[card.word_class] || 'text-gray-400 bg-gray-700/30'

  return (
    <div className="max-w-lg mx-auto">
      {/* Progress */}
      <div className="flex justify-between text-sm text-gray-500 dark:text-gray-400 mb-3">
        <span>Card {currentIndex + 1} of {cards.length}</span>
        <span>{Math.round(((currentIndex) / cards.length) * 100)}% done</span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-8">
        <div
          className="bg-blue-500 h-2 rounded-full transition-all duration-300"
          style={{ width: `${((currentIndex) / cards.length) * 100}%` }}
        />
      </div>

      {/* Flip card */}
      <div className="card-container" onClick={() => setIsFlipped(!isFlipped)}>
        <div className={`card-inner shadow-lg ${isFlipped ? 'is-flipped' : ''}`}>

          {/* Front */}
          <div className="card-face border-2 rounded-2xl p-8
                          flex flex-col justify-center items-center text-center
                          hover:border-blue-500/60 transition-colors
                          dark:border-gray-700 dark:bg-gray-800/90">
            <p className="text-gray-500 text-xs uppercase tracking-widest mb-4">German</p>
            {card.word_class && (
              <span className={`text-xs uppercase tracking-wider font-semibold px-2.5 py-0.5 rounded-full mb-3 ${wcStyle}`}>
                {card.word_class}
              </span>
            )}
            <h2 className="text-4xl font-bold text-blue-400">
              {card.gender && <span className="text-gray-400 text-2xl font-normal">{card.gender} </span>}
              {card.german_word}
            </h2>
            {card.plural_form && (
              <p className="text-gray-500 mt-2 text-sm">({card.plural_form})</p>
            )}
            <button
              onClick={(e) => { e.stopPropagation(); speak(card.german_word) }}
              className="mt-4 text-gray-500 hover:text-blue-400 transition-colors text-xl"
              title="Pronounce"
            >
              🔊
            </button>
            {card.gender_tip && (
              <div className="bg-blue-900/30 border border-blue-800/40 rounded-lg px-3 py-2 mt-4 text-xs text-blue-400">
                🔵 {card.gender_tip}
              </div>
            )}
            <p className="text-gray-600 text-xs mt-6">click to reveal</p>
          </div>

          {/* Back */}
          <div className="card-face card-back border-2 rounded-2xl p-8
                          flex flex-col justify-center items-center text-center
                          dark:border-gray-700 dark:bg-gray-800/90">
            <p className="text-gray-500 text-xs uppercase tracking-widest mb-4">English</p>
            <h2 className="text-3xl font-bold text-green-400 mb-4">
              {card.english_translation}
            </h2>
            <p className="text-gray-400 italic text-sm mb-2">{card.example_sentence_de}</p>
            <p className="text-gray-500 text-sm mb-4">{card.example_sentence_en}</p>
            {card.mnemonic && (
              <div className="bg-yellow-900/20 border border-yellow-800/30 rounded-lg p-3 text-sm text-yellow-400">
                💡 {card.mnemonic}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Rating buttons */}
      {isFlipped && (
        <div className="flex gap-3 mt-6">
          <button
            onClick={() => handleRate('hard')}
            className="flex-1 bg-red-900/30 border border-red-800/40 text-red-400
                       py-3 rounded-xl hover:bg-red-900/50 font-medium transition-all active:scale-95"
          >
            😰 Hard
          </button>
          <button
            onClick={() => handleRate('medium')}
            className="flex-1 bg-yellow-900/30 border border-yellow-800/40 text-yellow-400
                       py-3 rounded-xl hover:bg-yellow-900/50 font-medium transition-all active:scale-95"
          >
            🤔 Medium
          </button>
          <button
            onClick={() => handleRate('easy')}
            className="flex-1 bg-green-900/30 border border-green-800/40 text-green-400
                       py-3 rounded-xl hover:bg-green-900/50 font-medium transition-all active:scale-95"
          >
            😊 Easy
          </button>
        </div>
      )}
    </div>
  )
}

export default Study
