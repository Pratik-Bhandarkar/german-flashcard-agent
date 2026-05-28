import { useState } from 'react'
import { translateText, processTranslation } from '../services/api'

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
        new words become flashcards in the background.
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
                {pipelineResult.saved} new · {pipelineResult.skipped} already known
              </p>

              {pipelineResult.flashcards?.length === 0 && (
                <p className="text-gray-400 dark:text-gray-500 text-sm">
                  No new words — you already have all of these!
                </p>
              )}

              <div className="grid grid-cols-1 gap-4">
                {pipelineResult.flashcards?.map(card => (
                  <div
                    key={card.id}
                    className="border rounded-lg p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800"
                  >
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

                    <p className="text-gray-700 dark:text-gray-300 mt-1">{card.english_translation}</p>

                    {card.gender_tip && (
                      <p className="text-blue-500 dark:text-blue-400 text-xs mt-2">🔵 {card.gender_tip}</p>
                    )}

                    <p className="text-gray-500 dark:text-gray-400 text-sm mt-2 italic">
                      {card.example_sentence_de}
                    </p>
                    <p className="text-gray-400 dark:text-gray-500 text-sm">{card.example_sentence_en}</p>

                    {card.mnemonic && (
                      <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-2 mt-3 text-sm text-yellow-800 dark:text-yellow-400">
                        💡 {card.mnemonic}
                      </div>
                    )}

                    {card.tags?.length > 0 && (
                      <div className="flex gap-2 mt-3 flex-wrap">
                        {card.tags.map(tag => (
                          <span
                            key={tag}
                            className="bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs px-2 py-1 rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default Translate
