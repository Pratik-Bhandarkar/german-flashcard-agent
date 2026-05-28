import { useEffect, useState } from 'react'
import { getAllFlashcards, deleteFlashcard } from '../services/api'

function Home() {
  const [flashcards, setFlashcards] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { fetchFlashcards() }, [])

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
      setFlashcards(prev => prev.filter(card => card.id !== id))
    } catch (error) {
      console.error('Failed to delete flashcard:', error)
    }
  }

  if (loading) return (
    <div className="text-center text-gray-500 dark:text-gray-400 mt-20">Loading flashcards...</div>
  )

  if (flashcards.length === 0) return (
    <div className="text-center text-gray-500 dark:text-gray-400 mt-20">
      No flashcards yet. Go to Add Vocab to create some!
    </div>
  )

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 dark:text-white">
        Your Flashcards ({flashcards.length})
      </h2>

      <div className="grid grid-cols-1 gap-4">
        {flashcards.map(card => (
          <div
            key={card.id}
            className="border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow
                       dark:border-gray-700 dark:bg-gray-800"
          >
            <div className="flex justify-between items-start">
              <div>
                {card.word_class && (
                  <span className="text-xs uppercase tracking-widest text-gray-400 dark:text-gray-500 block mb-0.5">
                    {card.word_class}
                  </span>
                )}
                <span className="text-lg font-bold text-blue-700 dark:text-blue-400">
                  {card.gender && `${card.gender} `}{card.german_word}
                </span>
                {card.plural_form && (
                  <span className="text-gray-400 dark:text-gray-500 text-sm ml-2">
                    ({card.plural_form})
                  </span>
                )}
              </div>
              <button
                onClick={() => handleDelete(card.id)}
                className="text-red-400 hover:text-red-600 dark:text-red-500 dark:hover:text-red-400 text-sm"
              >
                Delete
              </button>
            </div>

            <p className="text-gray-700 dark:text-gray-300 mt-1">{card.english_translation}</p>

            {card.gender_tip && (
              <p className="text-blue-500 dark:text-blue-400 text-xs mt-2">🔵 {card.gender_tip}</p>
            )}

            <p className="text-gray-500 dark:text-gray-400 text-sm mt-2 italic">
              {card.example_sentence_de}
            </p>

            {card.tags && card.tags.length > 0 && (
              <div className="flex gap-2 mt-3 flex-wrap">
                {card.tags.map(tag => (
                  <span
                    key={tag}
                    className="bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400
                               text-xs px-2 py-1 rounded-full"
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
