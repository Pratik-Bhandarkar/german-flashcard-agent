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

// Fetch cards due for review today
export const getReviewCards = () =>
  api.get('/flashcards/review')

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