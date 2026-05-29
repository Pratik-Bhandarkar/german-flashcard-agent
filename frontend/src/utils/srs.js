const DAYS = { easy: 7, medium: 3, hard: 1 }

export function getNextReviewDate(difficulty) {
  const today = new Date()
  today.setDate(today.getDate() + DAYS[difficulty])
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
