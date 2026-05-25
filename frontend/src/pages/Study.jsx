// Study.jsx
// Flashcard study mode with flip animation and spaced repetition rating.
// Shows one card at a time — click to flip, then rate difficulty.

import { useEffect, useState } from 'react'
import { getAllFlashcards, updateFlashcard } from '../services/api'

// Calculate next review date based on difficulty rating
const getNextReviewDate = (difficulty) => {
  const today = new Date()
  const days = { easy: 7, medium: 3, hard: 1 }
  today.setDate(today.getDate() + days[difficulty])
  return today.toISOString().split('T')[0]
}

function Study() {
  const [cards, setCards] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)
  const [loading, setLoading] = useState(true)
  const [finished, setFinished] = useState(false)

  useEffect(() => {
    fetchCards()
  }, [])

  const fetchCards = async () => {
    try {
      const response = await getAllFlashcards()
      setCards(response.data)
    } catch (error) {
      console.error('Failed to fetch cards:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFlip = () => setIsFlipped(!isFlipped)

  const handleRate = async (difficulty) => {
    const card = cards[currentIndex]

    try {
      // Save difficulty and next review date to the database
      await updateFlashcard(card.id, {
        difficulty,
        next_review: getNextReviewDate(difficulty)
      })
    } catch (error) {
      console.error('Failed to update card:', error)
    }

    // Move to next card
    if (currentIndex + 1 >= cards.length) {
      setFinished(true)
    } else {
      setCurrentIndex(currentIndex + 1)
      setIsFlipped(false)
    }
  }

  if (loading) return (
    <div className="text-center text-gray-500 mt-20">
      Loading cards...
    </div>
  )

  if (cards.length === 0) return (
    <div className="text-center text-gray-500 mt-20">
      No cards to study. Add some vocab first!
    </div>
  )

  if (finished) return (
    <div className="text-center mt-20">
      <div className="text-5xl mb-4">🎉</div>
      <h2 className="text-2xl font-bold mb-2">Session Complete!</h2>
      <p className="text-gray-500 mb-6">
        You studied {cards.length} cards.
      </p>
      <button
        onClick={() => {
          setCurrentIndex(0)
          setIsFlipped(false)
          setFinished(false)
        }}
        className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
      >
        Study Again
      </button>
    </div>
  )

  const card = cards[currentIndex]

  return (
    <div className="max-w-lg mx-auto">
      {/* Progress indicator */}
      <div className="flex justify-between text-sm text-gray-500 mb-6">
        <span>Card {currentIndex + 1} of {cards.length}</span>
        <span>{card.tags?.join(', ')}</span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 mb-8">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all"
          style={{ width: `${((currentIndex + 1) / cards.length) * 100}%` }}
        />
      </div>

      {/* Flashcard — click to flip */}
      <div
        onClick={handleFlip}
        className="border-2 rounded-xl p-8 min-h-64 cursor-pointer
                   hover:border-blue-300 transition-colors shadow-md
                   flex flex-col justify-center items-center text-center"
      >
        {!isFlipped ? (
          // Front — German word
          <div>
            <p className="text-gray-400 text-sm mb-3">German</p>
            <h2 className="text-4xl font-bold text-blue-700">
              {card.gender && `${card.gender} `}{card.german_word}
            </h2>
            {card.plural_form && (
              <p className="text-gray-400 mt-2">({card.plural_form})</p>
            )}
            <p className="text-gray-400 text-sm mt-6">
              Click to reveal
            </p>
          </div>
        ) : (
          // Back — English translation and enrichment
          <div className="w-full">
            <p className="text-gray-400 text-sm mb-3">English</p>
            <h2 className="text-3xl font-bold text-green-700 mb-4">
              {card.english_translation}
            </h2>
            <p className="text-gray-600 italic text-sm mb-3">
              {card.example_sentence_de}
            </p>
            <p className="text-gray-500 text-sm mb-4">
              {card.example_sentence_en}
            </p>
            {card.mnemonic && (
              <div className="bg-yellow-50 rounded-lg p-3 text-sm text-yellow-800">
                💡 {card.mnemonic}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Rating buttons — only show after flip */}
      {isFlipped && (
        <div className="flex gap-3 mt-6">
          <button
            onClick={() => handleRate('hard')}
            className="flex-1 bg-red-100 text-red-700 py-3 rounded-lg
                       hover:bg-red-200 font-medium"
          >
            😰 Hard
          </button>
          <button
            onClick={() => handleRate('medium')}
            className="flex-1 bg-yellow-100 text-yellow-700 py-3 rounded-lg
                       hover:bg-yellow-200 font-medium"
          >
            🤔 Medium
          </button>
          <button
            onClick={() => handleRate('easy')}
            className="flex-1 bg-green-100 text-green-700 py-3 rounded-lg
                       hover:bg-green-200 font-medium"
          >
            😊 Easy
          </button>
        </div>
      )}
    </div>
  )
}

export default Study