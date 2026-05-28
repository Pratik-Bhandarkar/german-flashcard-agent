import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { activateBulk, activateLesson, activateWord, getLibraryWords } from '../services/api'

const LEVEL_STYLES = {
  A1: { bar: 'bg-green-500',   badge: 'bg-green-900/40 text-green-300',   topBorder: 'border-t-green-500' },
  A2: { bar: 'bg-emerald-500', badge: 'bg-emerald-900/40 text-emerald-300', topBorder: 'border-t-emerald-500' },
  B1: { bar: 'bg-blue-500',    badge: 'bg-blue-900/40 text-blue-300',      topBorder: 'border-t-blue-500' },
  B2: { bar: 'bg-violet-500',  badge: 'bg-violet-900/40 text-violet-300',  topBorder: 'border-t-violet-500' },
  C1: { bar: 'bg-amber-500',   badge: 'bg-amber-900/40 text-amber-300',    topBorder: 'border-t-amber-500' },
  C2: { bar: 'bg-rose-500',    badge: 'bg-rose-900/40 text-rose-300',      topBorder: 'border-t-rose-500' },
}

const WC_COLORS = {
  noun:      'text-blue-400 bg-blue-900/30',
  verb:      'text-green-400 bg-green-900/30',
  adjective: 'text-amber-400 bg-amber-900/30',
  adverb:    'text-purple-400 bg-purple-900/30',
}

const WC_LABELS = { noun: 'Noun', verb: 'Verb', adjective: 'Adj', adverb: 'Adv' }

function LibraryLevel() {
  const { level } = useParams()
  const levelUpper = level.toUpperCase()
  const styles = LEVEL_STYLES[levelUpper] || LEVEL_STYLES.B1

  const [data, setData]               = useState(null)
  const [loading, setLoading]         = useState(true)
  const [search, setSearch]           = useState('')
  const [lessonFilter, setLesson]     = useState('all')
  const [classFilter, setClass]       = useState('all')
  const [activating, setActivating]   = useState(new Set())
  const [selectMode, setSelectMode]   = useState(false)
  const [selected, setSelected]       = useState(new Set())
  const [bulkLoading, setBulkLoading] = useState(false)

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

  const handleBulkActivate = async () => {
    const wordIds = [...selected].filter(id => {
      const w = data.words.find(w => w.id === id)
      return w && !w.activated
    })
    if (!wordIds.length) return
    setBulkLoading(true)
    try {
      await activateBulk(level, wordIds)
      wordIds.forEach(id => updateWord(id, { activated: true }))
      setSelected(new Set())
      setSelectMode(false)
    } catch (err) {
      console.error(err)
    } finally {
      setBulkLoading(false)
    }
  }

  const toggleSelect = (wordId) => {
    setSelected(prev => {
      const s = new Set(prev)
      if (s.has(wordId)) s.delete(wordId)
      else s.add(wordId)
      return s
    })
  }

  const exitSelectMode = () => {
    setSelectMode(false)
    setSelected(new Set())
  }

  if (loading) return (
    <div className="text-center text-gray-500 mt-20">Loading words…</div>
  )
  if (!data) return null

  const pct = data.total_words > 0 ? Math.round((data.activated_words / data.total_words) * 100) : 0
  const unactivatedSelected = [...selected].filter(id => {
    const w = data.words.find(w => w.id === id)
    return w && !w.activated
  }).length

  return (
    <div className="pb-24">
      {/* Header */}
      <div className="mb-6">
        <Link to="/library" className="text-sm text-gray-500 hover:text-blue-400 mb-3 inline-block transition-colors">
          ← Library
        </Link>
        <div className="flex items-center gap-3 mb-1">
          <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${styles.badge}`}>{levelUpper}</span>
          <h2 className="text-2xl font-bold dark:text-white">{data.label}</h2>
        </div>
        <p className="text-sm text-gray-400 mb-2">
          {data.activated_words} of {data.total_words} words in your deck ({pct}%)
        </p>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div className={`${styles.bar} h-2 rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
        </div>
      </div>

      {/* Filters + Select toggle */}
      <div className="flex gap-2 mb-6 flex-wrap">
        <input
          type="text"
          placeholder="Search words…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 min-w-40 border rounded-lg px-3 py-2 text-sm
                     dark:bg-gray-800 dark:border-gray-600 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={lessonFilter}
          onChange={e => setLesson(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm
                     dark:bg-gray-800 dark:border-gray-600 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                     focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Types</option>
          {wordClasses.map(c => (
            <option key={c} value={c}>{WC_LABELS[c] || c}</option>
          ))}
        </select>
        <button
          onClick={() => selectMode ? exitSelectMode() : setSelectMode(true)}
          className={`border rounded-lg px-3 py-2 text-sm font-medium transition-colors
            ${selectMode
              ? 'bg-blue-600 border-blue-600 text-white'
              : 'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 hover:dark:border-gray-500'
            }`}
        >
          {selectMode ? 'Cancel' : 'Select'}
        </button>
      </div>

      {filteredWords.length === 0 && (
        <p className="text-center text-gray-500 mt-12">No words match your search.</p>
      )}

      {/* Lesson groups */}
      <div className="space-y-4">
        {[...lessonGroups.entries()].map(([lessonNum, words]) => {
          const addedInLesson = words.filter(w => w.activated).length
          const allAdded = addedInLesson === words.length

          return (
            <div key={lessonNum} className="border dark:border-gray-700 rounded-xl overflow-hidden">
              {/* Lesson header */}
              <div className="flex items-center justify-between px-4 py-3
                              bg-gray-800/60 border-b dark:border-gray-700">
                <div>
                  <span className="font-medium text-gray-200 text-sm">{words[0]?.lesson}</span>
                  <span className="text-xs text-gray-500 ml-2">{addedInLesson}/{words.length}</span>
                </div>
                {!allAdded && !selectMode && (
                  <button
                    onClick={() => handleActivateLesson(lessonNum)}
                    className="text-xs font-medium text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    + Add All
                  </button>
                )}
                {selectMode && (
                  <button
                    onClick={() => {
                      const ids = words.filter(w => !w.activated).map(w => w.id)
                      setSelected(prev => {
                        const s = new Set(prev)
                        ids.forEach(id => s.add(id))
                        return s
                      })
                    }}
                    className="text-xs font-medium text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    Select All
                  </button>
                )}
              </div>

              {/* Word rows */}
              <div className="divide-y dark:divide-gray-700/50">
                {words.map(word => {
                  const wcStyle = WC_COLORS[word.word_class] || 'text-gray-400 bg-gray-700/30'
                  const isSelected = selected.has(word.id)

                  return (
                    <div
                      key={word.id}
                      onClick={() => selectMode && !word.activated && toggleSelect(word.id)}
                      className={`flex items-center px-4 py-3 gap-3 transition-colors
                        ${selectMode && !word.activated ? 'cursor-pointer' : ''}
                        ${isSelected ? 'bg-blue-900/20' : 'hover:bg-gray-800/40'}`}
                    >
                      {selectMode && (
                        <input
                          type="checkbox"
                          checked={isSelected}
                          disabled={word.activated}
                          onChange={() => !word.activated && toggleSelect(word.id)}
                          onClick={e => e.stopPropagation()}
                          className="w-4 h-4 rounded accent-blue-500 shrink-0 cursor-pointer disabled:opacity-30"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <span className="font-semibold text-blue-400">
                          {word.gender && <span className="text-gray-400 font-normal text-sm">{word.gender} </span>}
                          {word.german_word}
                        </span>
                        {word.plural_form && (
                          <span className="text-gray-500 text-xs ml-1">({word.plural_form})</span>
                        )}
                      </div>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${wcStyle}`}>
                        {WC_LABELS[word.word_class] || word.word_class}
                      </span>
                      <span className="text-gray-300 text-sm flex-1 min-w-0 truncate">
                        {word.english_translation}
                      </span>
                      {!selectMode && (
                        <div className="w-16 shrink-0 text-right">
                          {word.activated ? (
                            <span className="text-xs font-medium text-green-400">✓ Added</span>
                          ) : (
                            <button
                              onClick={() => handleActivate(word)}
                              disabled={activating.has(word.id)}
                              className="text-xs font-medium text-blue-400 hover:text-blue-300
                                         disabled:opacity-50 transition-colors"
                            >
                              {activating.has(word.id) ? '…' : '+ Add'}
                            </button>
                          )}
                        </div>
                      )}
                      {selectMode && word.activated && (
                        <span className="text-xs font-medium text-green-400 w-16 text-right shrink-0">✓ Added</span>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>

      {/* Sticky bulk action bar */}
      {selectMode && selected.size > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur-sm
                        border-t dark:border-gray-700 px-4 py-3 z-50">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <span className="text-sm text-gray-300">
              {unactivatedSelected} word{unactivatedSelected !== 1 ? 's' : ''} to add
              {selected.size !== unactivatedSelected && ` (${selected.size - unactivatedSelected} already added)`}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setSelected(new Set())}
                className="text-sm text-gray-400 hover:text-gray-200 px-3 py-1.5 rounded-lg transition-colors"
              >
                Clear
              </button>
              <button
                onClick={handleBulkActivate}
                disabled={bulkLoading || unactivatedSelected === 0}
                className="bg-blue-600 hover:bg-blue-500 text-white text-sm px-5 py-1.5 rounded-lg
                           font-medium transition-colors disabled:opacity-50 active:scale-95"
              >
                {bulkLoading ? 'Adding…' : `Add ${unactivatedSelected} to Deck`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default LibraryLevel
