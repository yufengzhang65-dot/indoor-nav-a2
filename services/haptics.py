"""
Directional haptics (left/right/forward/arrive).

- Uses plyer.vibrator when available; otherwise no-op on desktop.
- vibrate_pattern(kind="forward", strength="normal"):
    spawns a short thread; 'strength' scales the base pattern.
"""
# from plyer import vibrator  # type: ignore
# BASE contains vibration patterns in milliseconds.

import threading, time
try:
    from plyer import vibrator
    HAVE = True
except Exception:
    HAVE = False

BASE = {
    "forward": [200],
    "left":    [120, 100, 120],
    "right":   [300, 120, 300],
    "arrive":  [600]
}

def vibrate_pattern(kind="forward", strength="normal"):
    seq = BASE.get(kind, [200])
    k = {"light": 0.6, "normal": 1.0, "strong": 1.5}.get(strength, 1.0)
    seq = [int(x * k) for x in seq]

    def _run():
        if not HAVE: return
        for i, dur in enumerate(seq):
            try:
                vibrator.vibrate(dur/1000.0)
            except Exception:
                pass
            if i < len(seq)-1:
                time.sleep(0.12)
    threading.Thread(target=_run, daemon=True).start()
