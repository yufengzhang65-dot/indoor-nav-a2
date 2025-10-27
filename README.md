# IndoorNav — Desktop-hosted Mobile Prototype (COMP826 A2)

Phone-sized Kivy app demonstrating a turn-by-turn indoor navigation flow with accessibility features and a full evaluation pipeline (logging + analysis scripts).

> **Why desktop-hosted?** Milestone 2 focuses on *evaluation and justification*. Running on a phone-sized desktop window lets us instrument precise logs and reproduce benchmarks. Hardware-specific features (vibration/battery) are treated as limitations and planned for Android validation in future work.

##  Features
- **Navigation flow**: Home → Settings → Navigate (Next / Reroute) → Arrived  
- **Accessibility**: high contrast, large text, graded haptics (light/normal/strong)  
- **Speech**: TTS with pre-warm; robust fallback (plyer → pyttsx3 → simulated)  
- **Logging**: per-event CSV logs for cold/warm/TTS/reroute and settings changes  
- **Evaluation**: scripts to generate P1–P3(+P7) charts and check acceptance

##  Tech Stack
Python 3.10+ · Kivy · Plyer · pyttsx3 · pandas · matplotlib · psutil

##  Project Structure
indoor_nav/
main.py
data/route.json
services/ (logger.py, tts_adapter.py, haptics.py, power_probe.py)
models/ (route_model.py)
viewmodels/ (nav_vm.py)
logs/ (auto-generated CSVs)
charts/ (analysis outputs)
analyze_logs.py
acceptance_eval.py
score_surveys.py
surveys/ (put MARS/SUS CSVs here)

## Getting Started (Windows / macOS)
```bash
# 1) create & activate venv
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

# 2) install deps
pip install -r requirements.txt
Windows PowerShell note: if activation is blocked, run
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force


##  Run the App
python main.py

Phone-sized window opens. Use Settings to toggle accessibility and optionally run TTS Prewarm. Use Navigate to tap Next Instruction and Simulate Reroute, then reach Arrived.
Logs are saved under logs/run_*.csv.


## Generate Charts & Check Acceptance
python analyze_logs.py      # P1–P3 (+ P7) -> charts/
python acceptance_eval.py   # prints pass/fail against targets

Acceptance thresholds
| Metric            |    Target |
| ----------------- | --------: |
| Cold start        | ≤ 1500 ms |
| Warm start        |  ≤ 800 ms |
| TTS start latency |  ≤ 500 ms |
| Reroute latency   | ≤ 1000 ms |


## A/B (Optional)
Collect 6 sessions: prewarm=ON × 3 (tap the button Run TTS Prewarm Benchmark in Settings on time) and OFF × 3 (don’t tap).
Then run:
python analyze_logs.py

The script prints per-session medians and an ON vs OFF comparison with a 95% CI.


## Usability (Optional for report P5/P6)
Place MARS/SUS CSVs under surveys/ and run:
python score_surveys.py
Outputs charts/P5_mars.png and charts/P6_sus.png.

## License
Academic/educational use only. Code is licensed under MIT. See LICENSE.
