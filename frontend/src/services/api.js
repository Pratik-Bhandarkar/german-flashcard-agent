// api.js
// All HTTP calls to the FastAPI backend live here.
// Components never call the API directly — they go through this service.

import axios from 'axios'

// Base URL for all API calls — matches our FastAPI server
const API_BASE_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Fetch all flashcards
export const getAllFlashcards = () =>
  api.get('/flashcards')

// Fetch cards due for review (capped at 20 by default; pass 0 for all)
export const getReviewCards = (limit = 20) =>
  api.get('/flashcards/review', { params: limit === 0 ? { limit: 0 } : {} })

// Process plain text through the pipeline
export const processText = (text, source, tags) =>
  api.post('/flashcards/process/text', { text, source, tags })

// Upload an image through the pipeline
export const processImage = (formData) =>
  api.post('/flashcards/process/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

// Update a flashcard's difficulty and next review date
export const updateFlashcard = (id, data) =>
  api.put(`/flashcards/${id}`, data)

// Delete a flashcard
export const deleteFlashcard = (id) =>
  api.delete(`/flashcards/${id}`)

// Instantly translate German text via DeepL (no pipeline)
export const translateText = (text) =>
  api.post('/flashcards/translate', { text })

// Run pipeline on German text and return new flashcards
export const processTranslation = (text, tags) =>
  api.post('/flashcards/process/translation', { text, tags })

// Library — all levels with progress stats
export const getLibraryLevels = () =>
  api.get('/library/levels')

// Library — all words for a level, with activated flag
export const getLibraryWords = (level, { lesson, word_class } = {}) => {
  const params = {}
  if (lesson !== undefined) params.lesson = lesson
  if (word_class !== undefined) params.word_class = word_class
  return api.get(`/library/${level}/words`, { params })
}

// Library — add a single word to the user's deck
export const activateWord = (level, wordId) =>
  api.post(`/library/${level}/${wordId}/activate`)

// Library — add all words in a lesson to the user's deck
export const activateLesson = (level, lessonNumber) =>
  api.post(`/library/${level}/activate-lesson`, { lesson_number: lessonNumber })

// Library — bulk add selected words to the user's deck
export const activateBulk = (level, wordIds) =>
  api.post(`/library/${level}/activate-bulk`, { word_ids: wordIds })

// Library — 3 daily words (rotates each day, unactivated first)
export const getWordsOfDay = () =>
  api.get('/library/words-of-day')

// Flashcard stats: due today, total, streak
export const getFlashcardStats = () =>
  api.get('/flashcards/stats')

// Translation deck — cards from the Translate page due for review
export const getTranslationCards = () =>
  api.get('/flashcards/translations/review')