import threading
import sys

try:
    import pyttsx3
except Exception:  # pragma: no cover - optional runtime dependency
    pyttsx3 = None

try:
    import speech_recognition as sr
except Exception:  # pragma: no cover - optional runtime dependency
    sr = None


class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer() if sr is not None else None
        self.microphone = sr.Microphone() if sr is not None else None
        self.speaker = self._create_speaker()
        self._lock = threading.Lock()

    def _create_speaker(self):
        if pyttsx3 is not None:
            try:
                return pyttsx3.init()
            except Exception:
                return None

        if sys.platform.startswith("win"):
            try:
                import win32com.client
                return win32com.client.Dispatch("SAPI.SpVoice")
            except Exception:
                return None

        return None

    def is_listening_supported(self):
        return self.recognizer is not None and self.microphone is not None

    def is_speaking_supported(self):
        return self.speaker is not None

    def speak(self, text):
        if not text or not self.is_speaking_supported():
            return

        try:
            if pyttsx3 is not None and self.speaker is not None:
                self.speaker.say(str(text))
                self.speaker.runAndWait()
                return

            if hasattr(self.speaker, "Speak"):
                self.speaker.Speak(str(text))
                return
        except Exception:
            pass

    def listen_for_command(self, timeout=8, phrase_time_limit=6):
        if not self.is_listening_supported():
            return ""

        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

            return self.recognizer.recognize_google(audio)
        except Exception:
            return ""

    def listen_for_query(self):
        self.speak("Listening for your search query.")
        query = self.listen_for_command()
        return query.strip() if query else ""

    def speak_results_summary(self, query, results):
        if not query:
            return

        if not results:
            self.speak(f"No results found for {query}.")
            return

        count = len(results)
        first_name = ""

        try:
            first_name = str(results[0][0]) if isinstance(results[0], (list, tuple)) and results[0] else ""
        except Exception:
            first_name = ""

        summary = f"I found {count} results for {query}."
        if first_name:
            summary += f" The top result is {first_name}."

        self.speak(summary)
