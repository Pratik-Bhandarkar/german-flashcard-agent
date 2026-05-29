export function speak(text) {
  if (!window.speechSynthesis) return
  window.speechSynthesis.cancel()
  const utt = new SpeechSynthesisUtterance(text)
  utt.lang = 'de-DE'
  utt.rate = 0.7
  window.speechSynthesis.speak(utt)
}
