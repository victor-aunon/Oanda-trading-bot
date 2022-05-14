from utils.tts import TTS


def test_tts():
    tts = TTS()
    assert tts.say("Testing") is None

    # Testing a non-existent language
    assert tts._set_language("klingon") is None

    # Testing a non-existent driver
    tts = TTS(driver="non-existent driver")  # -> Fallback to dummy driver
    assert tts.say("Testing") is None
