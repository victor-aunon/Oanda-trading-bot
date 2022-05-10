from utils.tts import TTS


def test_tts():
    tts = TTS()
    assert tts.say("Testing") is None
