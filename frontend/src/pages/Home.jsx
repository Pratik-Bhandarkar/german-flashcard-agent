// Home.jsx
// Displays all flashcards fetched from the API.
// Shows german word, translation, gender, tags and a delete button.

import { useEffect, useState } from 'react'
import { getAllFlashcards, deleteFlashcard } from '../services/api'

function Home() {
  // State — list of flashcards fetched from the API
  const [flashcards, setFlashcards] = useState([])
  // State — show a loading message while fetching
  const [loading, setLoading] = useState(true)

  // useEffect runs once when the page loads
  // This is where we fetch data from the API
  useEffect(() => {
    fetchFlashcards()
  }, [])

  const fetchFlashcards = async () => {
    try {
      const response = await getAllFlashcards()
      setFlashcards(response.data)
    } catch (error) {
      console.error('Failed to fetch flashcards:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    try {
      await deleteFlashcard(id)
      // Remove deleted card from state without refetching
      setFlashcards(flashcards.filter(card => card.id !== id))
    } catch (error) {
      console.error('Failed to delete flashcard:', error)
    }
  }

  if (loading) return (
    <div className="text-center text-gray-500 mt-20">
      Loading flashcards...
    </div>
  )

  if (flashcards.length === 0) return (
    <div className="text-center text-gray-500 mt-20">
      No flashcards yet. Go to Add Vocab to create some!
    </div>
  )

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">
        Your Flashcards ({flashcards.length})
      </h2>

      <div className="grid grid-cols-1 gap-4">
        {flashcards.map(card => (
          <div
            key={card.id}
            className="border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow"
          >
            {/* Top row — word and delete button */}
            <div className="flex justify-between items-start">
              <div>
                <span className="text-lg font-bold text-blue-700">
                  {card.gender && `${card.gender} `}{card.german_word}
                </span>
                {card.plural_form && (
                  <span className="text-gray-400 text-sm ml-2">
                    ({card.plural_form})
                  </span>
                )}
              </div>
              <button
                onClick={() => handleDelete(card.id)}
                className="text-red-400 hover:text-red-600 text-sm"
              >
                Delete
              </button>
            </div>

            {/* Translation */}
            <p className="text-gray-700 mt-1">
              {card.english_translation}
            </p>

            {/* Example sentence */}
            <p className="text-gray-500 text-sm mt-2 italic">
              {card.example_sentence_de}
            </p>

            {/* Tags */}
            {card.tags && card.tags.length > 0 && (
              <div className="flex gap-2 mt-3 flex-wrap">
                {card.tags.map(tag => (
                  <span
                    key={tag}
                    className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default Home