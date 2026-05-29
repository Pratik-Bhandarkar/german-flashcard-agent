import { useState, useEffect, useCallback } from 'react'
import { translateText, processTranslation, getTranslationCards, updateFlashcard } from '../services/api'
import { speak } from '../utils/speech'

const WC_COLORS = {
  noun: 'text-blue-400',
  verb: 'text-green-400',
  adjective: 'text-amber-400',
  adverb: 'text-purple-400',
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

function TranslationDeck() {
  const [cards, setCards] = useState([])
  const [loading, setLoading] = useState(true)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)
  const [done, setDone] = useState(false)
  const [open, setOpen] = useState(false)

  const fetchCards = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getTranslationCards()
      setCards(res.data)
      setCurrentIndex(0)
      setIsFlipped(false)
      setDone(false)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchCards() }, [fetchCards])

  const handleRate = async (difficulty) => {
    const card = cards[currentIndex]
    try {
      await updateFlashcard(card.id, {
        difficulty,
        next_review: getNextReviewDate(difficulty)
      })
      if (currentIndex + 1 >= cards.length) {
        setDone(true)
      } else {
        setCurrentIndex(i => i + 1)
        setIsFlipped(false)
      }
    } catch (err) {
      console.error('Failed to update card:', err)
    }
  }

  const dueCount = cards.length

  return (
    <div className="mt-10 border-t dark:border-gray-700 pt-8">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center justify-between w-full text-left group"
      >
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold dark:text-white">Translation Deck</h3>
          {!loading && dueCount > 0 && (
            <span className="bg-blue-600 text-white text-xs font-semibold px-2 py-0.5 rounded-full">
              {dueCount} due
            </span>
          )}
          {!loading && dueCount === 0 && (
            <span className="text-gray-500 text-xs">all caught up</span>
          )}
        </div>
        <span className="text-gray-500 group-hover:text-gray-300 transition-colors text-sm">
          {open ? '▲ hide' : '▼ review'}
        </span>
      </button>

      {open && (
        <div className="mt-6">
          {loading && (
            <p className="text-gray-500 text-sm">Loading...</p>
          )}

          {!loading && dueCount === 0 && (
            <div className="text-center py-8">
              <div className="text-4xl mb-3">✅</div>
              <p className="text-gray-400 text-sm">No translations due for review.</p>
            </div>
          )}

          {!loading && dueCount > 0 && !done && (
            <>
              <div className="flex justify-between text-xs text-gray-500 mb-2">
                <span>{currentIndex + 1} of {cards.length}</span>
                <span>{Math.round((currentIndex / cards.length) * 100)}% done</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-1.5 mb-5">
                <div
                  className="bg-blue-500 h-1.5 rounded-full transition-all"
                  style={{ width: `${(currentIndex / cards.length) * 100}%` }}
                />
              </div>

              {(() => {
                const card = cards[currentIndex]
                const wcColor = WC_COLORS[card.word_class] || 'text-gray-400'
                return (
                  <div className="card-container" onClick={() => setIsFlipped(f => !f)}>
                    <div className={`card-inner shadow-lg ${isFlipped ? 'is-flipped' : ''}`}>
                      <div className="card-face border-2 rounded-2xl p-8 flex flex-col justify-center items-center text-center
                                      hover:border-blue-500/60 transition-colors dark:border-gray-700 dark:bg-gray-800/90">
                        <p className="text-gray-500 text-xs uppercase tracking-widest mb-4">German</p>
                        {card.word_class && (
                          <span className={`text-xs uppercase tracking-wider font-semibold mb-3 ${wcColor}`}>
                            {card.word_class}
                          </span>
                        )}
                        <h2 className="text-4xl font-bold text-blue-400">
                          {card.gender && <span className="text-gray-400 text-2xl font-normal">{card.gender} </span>}
                          {card.german_word}
                        </h2>
                        {card.plural_form && <p className="text-gray-500 mt-2 text-sm">({card.plural_form})</p>}
                        <button
                          onClick={e => { e.stopPropagation(); speak(card.german_word) }}
                          className="mt-4 text-gray-500 hover:text-blue-400 transition-colors text-xl"
                          title="Pronounce"
                        >🔊</button>
                        {card.gender_tip && (
                          <div className="bg-blue-900/30 border border-blue-800/40 rounded-lg px-3 py-2 mt-4 text-xs text-blue-400">
                            🔵 {card.gender_tip}
                          </div>
                        )}
                        <p className="text-gray-600 text-xs mt-6">click to reveal</p>
                      </div>

                      <div className="card-face card-back border-2 rounded-2xl p-8 flex flex-col justify-center items-center text-center
                                      dark:border-gray-700 dark:bg-gray-800/90">
                        <p className="text-gray-500 text-xs uppercase tracking-widest mb-4">English</p>
                        <h2 className="text-3xl font-bold text-green-400 mb-4">{card.english_translation}</h2>
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
                )
              })()}

              {isFlipped && (
                <div className="flex gap-3 mt-6">
                  <button onClick={() => handleRate('hard')}
                    className="flex-1 bg-red-900/30 border border-red-800/40 text-red-400 py-3 rounded-xl hover:bg-red-900/50 font-medium transition-all active:scale-95">
                    😰 Hard
                  </button>
                  <button onClick={() => handleRate('medium')}
                    className="flex-1 bg-yellow-900/30 border border-yellow-800/40 text-yellow-400 py-3 rounded-xl hover:bg-yellow-900/50 font-medium transition-all active:scale-95">
                    🤔 Medium
                  </button>
                  <button onClick={() => handleRate('easy')}
                    className="flex-1 bg-green-900/30 border border-green-800/40 text-green-400 py-3 rounded-xl hover:bg-green-900/50 font-medium transition-all active:scale-95">
                    😊 Easy
                  </button>
                </div>
              )}
            </>
          )}

          {!loading && done && (
            <div className="text-center py-8">
              <div className="text-4xl mb-3">🎉</div>
              <p className="text-gray-300 font-semibold">All caught up!</p>
              <button
                onClick={fetchCards}
                className="mt-4 text-sm text-blue-400 hover:underline"
              >
                Refresh
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Translate() {
  const [text, setText] = useState('')
  const [tags, setTags] = useState('')
  const [translating, setTranslating] = useState(false)
  const [pipelineLoading, setPipelineLoading] = useState(false)
  const [translation, setTranslation] = useState(null)
  const [pipelineResult, setPipelineResult] = useState(null)
  const [error, setError] = useState(null)
  const [pipelineError, setPipelineError] = useState(null)

  const handleTranslate = async () => {
    if (!text.trim()) return
    const tagsArray = tags.split(',').map(t => t.trim()).filter(t => t)
    setTranslating(true)
    setPipelineLoading(true)
    setTranslation(null)
    setPipelineResult(null)
    setError(null)
    setPipelineError(null)

    const translationPromise = translateText(text)
    const pipelinePromise = processTranslation(text, tagsArray)

    try {
      const res = await translationPromise
      setTranslation(res.data.translation)
    } catch (err) {
      setError('Translation failed. Is the backend running?')
    } finally {
      setTranslating(false)
    }

    try {
      const res = await pipelinePromise
      setPipelineResult(res.data)
    } catch (err) {
      setPipelineError('Failed to generate flashcards.')
    } finally {
      setPipelineLoading(false)
    }
  }

  const inputClass = "w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
  const labelClass = "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-2 dark:text-white">Translate & Learn</h2>
      <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">
        Paste a German sentence or paragraph. Translation appears instantly —
        new words go into your Translation Deck, separate from your main study queue.
      </p>

      <div className="mb-4">
        <label className={labelClass}>Tags (optional, comma separated)</label>
        <input
          type="text"
          value={tags}
          onChange={e => setTags(e.target.value)}
          placeholder="e.g. B1, travel, reading"
          className={inputClass}
        />
      </div>

      <div className="mb-4">
        <label className={labelClass}>German text</label>
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Der Hund läuft schnell durch den Park..."
          className={`${inputClass} h-36 resize-none`}
        />
        <button
          onClick={handleTranslate}
          disabled={translating || pipelineLoading || !text.trim()}
          className="mt-2 bg-blue-600 text-white px-6 py-2 rounded-lg
                     hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {translating ? 'Translating...' : 'Translate'}
        </button>
      </div>

      {error && (
        <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {translation && (
        <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <p className="text-xs uppercase tracking-widest text-blue-400 dark:text-blue-500 mb-2">Translation</p>
          <p className="text-blue-900 dark:text-blue-300 text-lg">{translation}</p>
        </div>
      )}

      {(pipelineLoading || pipelineResult || pipelineError) && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-3 dark:text-white">New Words Found</h3>

          {pipelineLoading && (
            <div className="text-blue-600 dark:text-blue-400 text-sm">
              ⏳ Finding new words and generating flashcards...
            </div>
          )}

          {pipelineError && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-400 text-sm">
              {pipelineError}
            </div>
          )}

          {pipelineResult && (
            <>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                {pipelineResult.saved} added to Translation Deck · {pipelineResult.skipped} already known
              </p>

              {pipelineResult.flashcards?.length === 0 && (
                <p className="text-gray-400 dark:text-gray-500 text-sm">
                  No new words — you already have all of these!
                </p>
              )}

              <div className="grid grid-cols-1 gap-4">
                {pipelineResult.flashcards?.map(card => (
                  <div key={card.id} className="border rounded-lg p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
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
                        <span className="text-gray-400 dark:text-gray-500 text-sm ml-2">({card.plural_form})</span>
                      )}
                    </div>
                    <p className="text-gray-700 dark:text-gray-300 mt-1">{card.english_translation}</p>
                    {card.gender_tip && (
                      <p className="text-blue-500 dark:text-blue-400 text-xs mt-2">🔵 {card.gender_tip}</p>
                    )}
                    <p className="text-gray-500 dark:text-gray-400 text-sm mt-2 italic">{card.example_sentence_de}</p>
                    <p className="text-gray-400 dark:text-gray-500 text-sm">{card.example_sentence_en}</p>
                    {card.mnemonic && (
                      <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-2 mt-3 text-sm text-yellow-800 dark:text-yellow-400">
                        💡 {card.mnemonic}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      <TranslationDeck />
    </div>
  )
}

export default Translate
