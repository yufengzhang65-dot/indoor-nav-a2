"""
Battery sampler (optional).

- battery_pct() -> int|None:
    returns battery % if the platform exposes it (via psutil),
    otherwise returns None.
"""

try:
    import psutil
    HAVE = True
except Exception:
    HAVE = False

def battery_pct():
    if not HAVE: return None
    b = psutil.sensors_battery()
    return None if b is None else int(b.percent)
