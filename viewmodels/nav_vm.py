"""
NavViewModel — core interaction logic

Public API:
- next_step(on_text, on_progress) -> "continue"|"arrived"
    * Logs click_next, TTS start latency, and plays haptics
- reroute(on_text, on_progress, compute_ms=300)
    * Simulates a reroute computation; logs reroute_latency_ms

Notes:
- self.settings expects dict keys: contrast, textscale, haptic_strength, persona
- All latency values are recorded in milliseconds for evaluation scripts.
"""
# _on_start callback logs latency: tap Next -> TTS callback started
# Use max(1, ...) to avoid 0 ms floor in integer rounding.

import time
from services.logger import log
from services.tts_adapter import speak_async
from services.haptics import vibrate_pattern

class NavViewModel:
    def __init__(self, steps, settings):
        self.steps = steps
        self.idx = 0
        self._click_t0 = None
        self.settings = settings  # {"contrast","textscale","haptic_strength","persona"}

    def next_step(self, on_text, on_progress):
        if self.idx >= len(self.steps):
            return "arrived"
        self._click_t0 = time.perf_counter()

        step = self.steps[self.idx]
        on_text(step["text"])
        on_progress(self.idx+1, len(self.steps))
        log("click_next", f"step_{step['id']}")

        def _on_start(label, t0):
            if self._click_t0:
                latency_ms = max(1, int((time.perf_counter() - self._click_t0) * 1000))
                log("tts_start_latency_ms", label, latency_ms)

        def _on_done(label, t0, t1):
            dur = int((t1 - t0)*1000); log("tts_done_ms", label, dur)

        speak_async(step["text"], _on_start, _on_done, f"step_{step['id']}")
        vibrate_pattern(step.get("type","forward"), self.settings.get("haptic_strength","normal"))
        self.idx += 1
        return "arrived" if self.idx >= len(self.steps) else "continue"

    def reroute(self, on_text, on_progress, compute_ms=300):
        self._click_t0 = time.perf_counter()
        log("click_reroute")
        time.sleep(compute_ms/1000.0)
        latency = int((time.perf_counter()-self._click_t0)*1000)
        log("reroute_latency_ms", "reroute", latency)
        self.idx = 0
        on_progress(self.idx, len(self.steps))
        txt = "Recalculating route, please return to the corridor and proceed."
        on_text(txt); speak_async(txt, None, None, "reroute")
        vibrate_pattern("forward", self.settings.get("haptic_strength","normal"))
