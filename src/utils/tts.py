import pyttsx3


class TTS:
    def __init__(self, language="EN-US", rate=120) -> None:
        try:
            self.engine = pyttsx3.init(debug=False)
            self.engine.setProperty("rate", rate)
            # Select language voice
            self._set_language(language)
        except Exception as e:
            print(e)
            self.engine = pyttsx3.init("dummy", debug=False)

    def _set_language(self, language):
        try:
            voice = [
                v for v in self.engine.getProperty("voices") if language
                in v.id
            ][0]
            self.engine.setProperty("voice", voice.id)
        except KeyError:
            print(f"Could not find TTS language {language}")
            pass

    def say(self, message) -> None:
        self.engine.startLoop(False)
        self.engine.say(message)
        self.engine.iterate()
        self.engine.endLoop()
