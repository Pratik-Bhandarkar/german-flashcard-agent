import { useRef, useState } from 'react'
import { processText, processImage } from '../services/api'

function Add() {
  const fileInputRef = useRef(null)
  const [text, setText] = useState('')
  const [source, setSource] = useState('')
  const [tags, setTags] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleTextSubmit = async () => {
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const tagsArray = tags.split(',').map(t => t.trim()).filter(t => t)
      const response = await processText(text, source || 'manual input', tagsArray)
      setResult(response.data)
      setText('')
    } catch (err) {
      setError('Failed to process text. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const handleImageUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('source', source || 'image upload')
      formData.append('tags', tags)
      const response = await processImage(formData)
      setResult(response.data)
    } catch (err) {
      setError('Failed to process image. Is the backend running?')
    } finally {
      setLoading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const inputClass = "w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
  const labelClass = "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-6 dark:text-white">Add Vocabulary</h2>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className={labelClass}>Source (optional)</label>
          <input
            type="text"
            value={source}
            onChange={e => setSource(e.target.value)}
            placeholder="e.g. Kapitel 9, Berlin trip"
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Tags (comma separated)</label>
          <input
            type="text"
            value={tags}
            onChange={e => setTags(e.target.value)}
            placeholder="e.g. B1, nouns, travel"
            className={inputClass}
          />
        </div>
      </div>

      <div className="mb-4">
        <label className={labelClass}>Paste vocabulary list</label>
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Hund, Katze, Bahnhof, laufen, schön..."
          className={`${inputClass} h-32 resize-none`}
        />
        <button
          onClick={handleTextSubmit}
          disabled={loading || !text.trim()}
          className="mt-2 bg-blue-600 text-white px-6 py-2 rounded-lg
                     hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Processing...' : 'Generate Flashcards'}
        </button>
      </div>

      <div className="flex items-center gap-4 my-6">
        <hr className="flex-1 dark:border-gray-700" />
        <span className="text-gray-400 dark:text-gray-500 text-sm">or upload an image</span>
        <hr className="flex-1 dark:border-gray-700" />
      </div>

      <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
        <p className="text-gray-500 dark:text-gray-400 mb-3">
          Upload a photo of a German vocab list
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,.pdf"
          onChange={handleImageUpload}
          disabled={loading}
          className="text-sm dark:text-gray-400"
        />
      </div>

      {loading && (
        <div className="mt-6 text-center text-blue-600 dark:text-blue-400">
          ⏳ Running pipeline — this may take a minute...
        </div>
      )}

      {error && (
        <div className="mt-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <p className="text-green-700 dark:text-green-400 font-medium">✅ {result.message}</p>
          <p className="text-green-600 dark:text-green-500 text-sm mt-1">
            Saved: {result.saved} | Skipped: {result.skipped}
          </p>
        </div>
      )}
    </div>
  )
}

export default Add
