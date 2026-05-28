import { useEffect, useState } from 'react'
import { getReviewCards, getAllFlashcards, updateFlashcard } from '../services/api'

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

  const handleRate = async (difficulty) => {
    const card = cards[currentIndex]
    try {
      await updateFlashcard(card.id, {
        difficulty,
        next_review: getNextReviewDate(difficulty)
      })
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
    <div className="text-center text-gray-500 dark:text-gray-400 mt-20">Loading cards...</div>
  )

  if (cards.length === 0) return (
    <div className="text-center text-gray-500 dark:text-gray-400 mt-20">
      <p className="mb-4">No cards due for review today.</p>
      <button
        onClick={async () => {
          setLoading(true)
          try {
            const response = await getAllFlashcards()
            setCards(response.data)
          } catch (error) {
            console.error('Failed to fetch all cards:', error)
          } finally {
            setLoading(false)
          }
        }}
        className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
      >
        Study All Cards Anyway
      </button>
    </div>
  )

  if (finished) return (
    <div className="text-center mt-20">
      <div className="text-5xl mb-4">🎉</div>
      <h2 className="text-2xl font-bold mb-2 dark:text-white">Session Complete!</h2>
      <p className="text-gray-500 dark:text-gray-400 mb-6">You studied {cards.length} cards.</p>
      <div className="flex gap-3 justify-center">
        <button
          onClick={() => { setCurrentIndex(0); setIsFlipped(false); setFinished(false) }}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
        >
          Study Again
        </button>
        <button
          onClick={() => { setCurrentIndex(0); setIsFlipped(false); setFinished(false); fetchCards() }}
          className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-6 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
        >
          New Session
        </button>
      </div>
    </div>
  )

  const card = cards[currentIndex]

  return (
    <div className="max-w-lg mx-auto">
      {/* Progress */}
      <div className="flex justify-between text-sm text-gray-500 dark:text-gray-400 mb-6">
        <span>Card {currentIndex + 1} of {cards.length}</span>
        <span>{card.tags?.join(', ')}</span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-8">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all"
          style={{ width: `${((currentIndex + 1) / cards.length) * 100}%` }}
        />
      </div>

      {/* Flip card */}
      <div className="card-container" onClick={() => setIsFlipped(!isFlipped)}>
        <div className={`card-inner shadow-md ${isFlipped ? 'is-flipped' : ''}`}>

          {/* Front */}
          <div className="card-face border-2 rounded-xl p-8
                          flex flex-col justify-center items-center text-center
                          hover:border-blue-300 dark:hover:border-blue-500 transition-colors
                          dark:border-gray-600 dark:bg-gray-800">
            <p className="text-gray-400 dark:text-gray-500 text-sm mb-3">German</p>
            {card.word_class && (
              <p className="text-xs uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-2">
                {card.word_class}
              </p>
            )}
            <h2 className="text-4xl font-bold text-blue-700 dark:text-blue-400">
              {card.gender && `${card.gender} `}{card.german_word}
            </h2>
            {card.plural_form && (
              <p className="text-gray-400 dark:text-gray-500 mt-2">({card.plural_form})</p>
            )}
            {card.gender_tip && (
              <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg px-3 py-2 mt-4 text-xs text-blue-600 dark:text-blue-400">
                🔵 {card.gender_tip}
              </div>
            )}
            <p className="text-gray-400 dark:text-gray-500 text-sm mt-6">Click to reveal</p>
          </div>

          {/* Back */}
          <div className="card-face card-back border-2 rounded-xl p-8
                          flex flex-col justify-center items-center text-center
                          dark:border-gray-600 dark:bg-gray-800">
            <p className="text-gray-400 dark:text-gray-500 text-sm mb-3">English</p>
            <h2 className="text-3xl font-bold text-green-700 dark:text-green-400 mb-4">
              {card.english_translation}
            </h2>
            <p className="text-gray-600 dark:text-gray-400 italic text-sm mb-3">
              {card.example_sentence_de}
            </p>
            <p className="text-gray-500 dark:text-gray-500 text-sm mb-4">
              {card.example_sentence_en}
            </p>
            {card.mnemonic && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 text-sm text-yellow-800 dark:text-yellow-400">
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
            className="flex-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400
                       py-3 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 font-medium"
          >
            😰 Hard
          </button>
          <button
            onClick={() => handleRate('medium')}
            className="flex-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400
                       py-3 rounded-lg hover:bg-yellow-200 dark:hover:bg-yellow-900/50 font-medium"
          >
            🤔 Medium
          </button>
          <button
            onClick={() => handleRate('easy')}
            className="flex-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400
                       py-3 rounded-lg hover:bg-green-200 dark:hover:bg-green-900/50 font-medium"
          >
            😊 Easy
          </button>
        </div>
      )}
    </div>
  )
}

export default Study
