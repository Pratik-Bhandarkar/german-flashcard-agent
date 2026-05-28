import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { activateLesson, activateWord, getLibraryWords } from '../services/api'

const LEVEL_STYLES = {
  A1: { bar: 'bg-green-500',  badge: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300' },
  A2: { bar: 'bg-emerald-500', badge: 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300' },
  B1: { bar: 'bg-blue-500',   badge: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300' },
  B2: { bar: 'bg-violet-500', badge: 'bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300' },
  C1: { bar: 'bg-amber-500',  badge: 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300' },
  C2: { bar: 'bg-rose-500',   badge: 'bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300' },
}

const WORD_CLASS_LABELS = { noun: 'Noun', verb: 'Verb', adjective: 'Adj', adverb: 'Adv' }

function LibraryLevel() {
  const { level } = useParams()
  const levelUpper = level.toUpperCase()
  const styles = LEVEL_STYLES[levelUpper] || LEVEL_STYLES.B1

  const [data, setData]           = useState(null)
  const [loading, setLoading]     = useState(true)
  const [search, setSearch]       = useState('')
  const [lessonFilter, setLesson] = useState('all')
  const [classFilter, setClass]   = useState('all')
  const [activating, setActivating] = useState(new Set())

  useEffect(() => {
    setLoading(true)
    getLibraryWords(level)
      .then(r => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [level])

  const { lessons, wordClasses, filteredWords, lessonGroups } = useMemo(() => {
    if (!data) return { lessons: [], wordClasses: [], filteredWords: [], lessonGroups: new Map() }

    const lessons = [...new Map(
      data.words.map(w => [w.lesson_number, { number: w.lesson_number, label: w.lesson }])
    ).values()].sort((a, b) => a.number - b.number)

    const wordClasses = [...new Set(data.words.map(w => w.word_class).filter(Boolean))].sort()

    const q = search.toLowerCase()
    const filteredWords = data.words.filter(w => {
      if (lessonFilter !== 'all' && w.lesson_number !== Number(lessonFilter)) return false
      if (classFilter !== 'all' && w.word_class !== classFilter) return false
      if (q && !w.german_word.toLowerCase().includes(q) && !w.english_translation.toLowerCase().includes(q)) return false
      return true
    })

    const lessonGroups = new Map()
    for (const w of filteredWords) {
      if (!lessonGroups.has(w.lesson_number)) lessonGroups.set(w.lesson_number, [])
      lessonGroups.get(w.lesson_number).push(w)
    }

    return { lessons, wordClasses, filteredWords, lessonGroups }
  }, [data, search, lessonFilter, classFilter])

  const updateWord = (wordId, patch) => {
    setData(prev => ({
      ...prev,
      activated_words: prev.activated_words + (patch.activated ? 1 : 0),
      words: prev.words.map(w => w.id === wordId ? { ...w, ...patch } : w),
    }))
  }

  const handleActivate = async (word) => {
    setActivating(prev => new Set(prev).add(word.id))
    try {
      await activateWord(level, word.id)
      updateWord(word.id, { activated: true })
    } catch (err) {
      if (err.response?.status === 409) updateWord(word.id, { activated: true })
      else console.error(err)
    } finally {
      setActivating(prev => { const s = new Set(prev); s.delete(word.id); return s })
    }
  }

  const handleActivateLesson = async (lessonNumber) => {
    const words = lessonGroups.get(lessonNumber) || []
    const unactivated = words.filter(w => !w.activated)
    unactivated.forEach(w => setActivating(prev => new Set(prev).add(w.id)))
    try {
      await activateLesson(level, lessonNumber)
      unactivated.forEach(w => updateWord(w.id, { activated: true }))
    } catch (err) {
      console.error(err)
    } finally {
      unactivated.forEach(w => setActivating(prev => { const s = new Set(prev); s.delete(w.id); return s }))
    }
  }

  if (loading) return (
    <div className="text-center text-gray-500 dark:text-gray-400 mt-20">Loading words...</div>
  )
  if (!data) return null

  const pct = data.total_words > 0 ? Math.round((data.activated_words / data.total_words) * 100) : 0

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <Link to="/library" className="text-sm text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 mb-3 inline-block">
          &larr; Library
        </Link>
        <div className="flex items-center gap-3 mb-1">
          <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${styles.badge}`}>{levelUpper}</span>
          <h2 className="text-2xl font-bold dark:text-white">{data.label}</h2>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
          {data.activated_words} of {data.total_words} words in your deck ({pct}%)
        </p>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div className={`${styles.bar} h-2 rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6 flex-wrap">
        <input
          type="text"
          placeholder="Search words..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 min-w-48 border rounded-lg px-3 py-2 text-sm
                     dark:bg-gray-800 dark:border-gray-600 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
        <select
          value={lessonFilter}
          onChange={e => setLesson(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm
                     dark:bg-gray-800 dark:border-gray-600 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          <option value="all">All Lessons</option>
          {lessons.map(l => (
            <option key={l.number} value={l.number}>{l.label}</option>
          ))}
        </select>
        <select
          value={classFilter}
          onChange={e => setClass(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm
                     dark:bg-gray-800 dark:border-gray-600 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          <option value="all">All Types</option>
          {wordClasses.map(c => (
            <option key={c} value={c}>{WORD_CLASS_LABELS[c] || c}</option>
          ))}
        </select>
      </div>

      {filteredWords.length === 0 && (
        <p className="text-center text-gray-500 dark:text-gray-400 mt-12">No words match your search.</p>
      )}

      {/* Lesson groups */}
      <div className="space-y-6">
        {[...lessonGroups.entries()].map(([lessonNum, words]) => {
          const addedInLesson = words.filter(w => w.activated).length
          const allAdded = addedInLesson === words.length

          return (
            <div key={lessonNum} className="border dark:border-gray-700 rounded-xl overflow-hidden">
              {/* Lesson header */}
              <div className="flex items-center justify-between px-4 py-3
                              bg-gray-50 dark:bg-gray-800/60 border-b dark:border-gray-700">
                <div>
                  <span className="font-medium text-gray-800 dark:text-gray-100 text-sm">
                    {words[0]?.lesson}
                  </span>
                  <span className="text-xs text-gray-400 dark:text-gray-500 ml-2">
                    {addedInLesson}/{words.length} added
                  </span>
                </div>
                {!allAdded && (
                  <button
                    onClick={() => handleActivateLesson(lessonNum)}
                    className="text-xs font-medium text-blue-600 dark:text-blue-400
                               hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
                  >
                    + Add All
                  </button>
                )}
              </div>

              {/* Word rows */}
              <div className="divide-y dark:divide-gray-700/60">
                {words.map(word => (
                  <div key={word.id}
                       className="flex items-center px-4 py-3 gap-3
                                  hover:bg-gray-50 dark:hover:bg-gray-800/40 transition-colors">
                    <div className="flex-1 min-w-0">
                      <span className="font-semibold text-blue-700 dark:text-blue-400">
                        {word.gender && `${word.gender} `}{word.german_word}
                      </span>
                      {word.plural_form && (
                        <span className="text-gray-400 dark:text-gray-500 text-sm ml-1">
                          ({word.plural_form})
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-400 dark:text-gray-500 w-14 shrink-0">
                      {WORD_CLASS_LABELS[word.word_class] || word.word_class}
                    </span>
                    <span className="text-gray-600 dark:text-gray-300 text-sm flex-1 min-w-0 truncate">
                      {word.english_translation}
                    </span>
                    <div className="w-20 shrink-0 text-right">
                      {word.activated ? (
                        <span className="text-xs font-medium text-green-600 dark:text-green-400">
                          ✓ Added
                        </span>
                      ) : (
                        <button
                          onClick={() => handleActivate(word)}
                          disabled={activating.has(word.id)}
                          className="text-xs font-medium text-blue-600 dark:text-blue-400
                                     hover:text-blue-800 dark:hover:text-blue-300
                                     disabled:opacity-50 transition-colors"
                        >
                          {activating.has(word.id) ? '...' : '+ Add'}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default LibraryLevel
