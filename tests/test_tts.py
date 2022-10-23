# Locals
from oandatradingbot.utils.tts import TTS


def test_tts():
    tts = TTS()
    tts.say("Testing")  # -> Should hear testing through speaker


def test_return_false_when_language_is_not_in_system():
    tts = TTS()
    assert tts._set_language("klingon") is False


def test_driver_is_dummy():
    # Testing a non-existent driver
    tts = TTS(driver="non-existent driver")  # -> Fallback to dummy driver
    assert "dummy" in tts.engine.getProperty("voice").id
