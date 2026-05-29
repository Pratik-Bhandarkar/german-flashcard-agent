let _pendingTimer = null

export function speak(text) {
  if (!window.speechSynthesis) return
  window.speechSynthesis.cancel()
  clearTimeout(_pendingTimer)
  // Chrome bug: cancel() is async — delay speak until it settles
  _pendingTimer = setTimeout(() => {
    const utt = new SpeechSynthesisUtterance(text)
    utt.lang = 'de-DE'
    utt.rate = 0.6
    window.speechSynthesis.speak(utt)
    _pendingTimer = null
  }, 150)
}

export function cancelSpeech() {
  clearTimeout(_pendingTimer)
  _pendingTimer = null
  if (window.speechSynthesis) window.speechSynthesis.cancel()
}
