export function speak(text) {
  if (!window.speechSynthesis) return
  window.speechSynthesis.cancel()
  // Chrome bug: cancel() is async — delay speak until it settles
  setTimeout(() => {
    const utt = new SpeechSynthesisUtterance(text)
    utt.lang = 'de-DE'
    utt.rate = 0.7
    window.speechSynthesis.speak(utt)
  }, 150)
}
