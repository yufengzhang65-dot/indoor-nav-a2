"""
TTS adapter with robust fallbacks.

Order of attempts:
1) plyer.tts (mobile-friendly; may be NotImplemented on desktop)
2) pyttsx3 (cross-platform speech engine)
3) fallback sleep() to simulate speech duration

- speak_async(text, on_start, on_done, label):
    runs in a background thread; never raises to caller.
- prewarm(label): triggers a minimal utterance to warm caches.
"""
# If your editor flags plyer imports, it's safe to silence:
# from plyer import tts as plyer_tts  # type: ignore
"""
TTS adapter with robust fallbacks.

Order of attempts:
1) plyer.tts (mobile-friendly; may be NotImplemented on desktop)
2) pyttsx3 (cross-platform speech engine)
3) fallback sleep() to simulate speech duration

- speak_async(text, on_start, on_done, label):
    runs in a background thread; never raises to caller.
- prewarm(label): triggers a minimal utterance to warm caches.
"""
# If your editor flags plyer imports, it's safe to silence:
# from plyer import tts as plyer_tts  # type: ignore

import threading, time
from services.logger import log

try:
    from plyer import tts as plyer_tts
    HAVE_PLYER = True
except Exception:
    HAVE_PLYER = False

try:
    import pyttsx3
    engine = pyttsx3.init()
    HAVE_PYTT = True
except Exception:
    HAVE_PYTT = False
    engine = None

def _speak_with_plyer(text: str) -> bool:
    plyer_tts.speak(text)  
    return True

def _speak_with_pyttsx3(text: str) -> bool:
    if not (HAVE_PYTT and engine):
        return False
    engine.say(text)
    engine.runAndWait()
    return True

def speak_async(text: str, on_start=None, on_done=None, label="tts"):
    def _run():
        t0 = time.perf_counter()
        if on_start:
            on_start(label, t0)
        try:
            played = False
            if HAVE_PLYER:
                try:
                    _speak_with_plyer(text)
                    played = True
                except Exception:
                    played = False  
            if not played and HAVE_PYTT:
                try:
                    _speak_with_pyttsx3(text)
                    played = True
                except Exception:
                    played = False
            if not played:
                time.sleep(0.4)
        finally:
            if on_done:
                on_done(label, t0, time.perf_counter())
    threading.Thread(target=_run, daemon=True).start()

def prewarm(label="tts_prewarm_ms"):
    t0 = time.perf_counter()
    speak_async("Ready", None, None, label)
    time.sleep(0.05)
    return int((time.perf_counter() - t0) * 1000)
