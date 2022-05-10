# Packages
import pyttsx3


class TTS:
    def __init__(self, language="EN-US", rate=120) -> None:
        self.engine = pyttsx3.init(debug=False)
        self.engine.setProperty("rate", rate)
        # Select language voice
        voice = [
            v for v in self.engine.getProperty("voices") if language in v.id
        ][0]
        self.engine.setProperty("voice", voice.id)

    def say(self, message) -> None:
        self.engine.startLoop(False)
        self.engine.say(message)
        self.engine.iterate()
        self.engine.endLoop()
