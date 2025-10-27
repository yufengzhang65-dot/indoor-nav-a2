"""
IndoorNav — Kivy desktop-hosted mobile prototype (COMP826 A2)

Purpose
-------
Phone-sized Kivy app that demonstrates the navigation flow and logs
performance metrics for evaluation.

Screens
-------
- Home: entry + link to Settings / Navigate.
- Settings: accessibility toggles (contrast, text size, haptic strength)
  and a "Run TTS Prewarm Benchmark" button.
- Navigate: "Next Instruction" + "Simulate Reroute" controls.
- Arrived: completion state.

Key logging events
------------------
- cold_start_ms: App.on_start() -> marks first frame visible.
- warm_start_ms: Home.tap(Start) -> Navigate.on_enter().
- tts_start_latency_ms: tap Next -> TTS callback started (VM).
- reroute_latency_ms: tap Reroute -> reroute prompt ready (VM).
- settings_*: when an accessibility setting changes.
- tts_prewarm_ms: duration of prewarm call.

Notes
-----
Window is set to phone size so screenshots look like a mobile app.
This is a desktop-hosted prototype; haptics/battery may be unavailable
on PCs and are treated as limitations in the report.
"""
# Phone-sized window for "mobile-like" screenshots
# Window.size = (390, 844)

# Inside Home.start_nav(): log click and capture NAV start timestamp
# Inside Navigate.on_enter(): compute/Log warm_start_ms

# In Settings.run_prewarm(): calling prewarm() writes tts_prewarm_ms

import time
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.spinner import Spinner

from services.logger import log, APP_T0
from models.route_model import RouteModel
from viewmodels.nav_vm import NavViewModel
from services.tts_adapter import prewarm

NAV_T0 = None

# 手机比例窗口（截图更像移动端）
Window.size = (390, 844)

DEFAULT_SETTINGS = {
    "contrast": "normal",
    "textscale": "normal",
    "haptic_strength": "normal",
    "persona": "blind"
}

# 可选：电量
try:
    from services.power_probe import battery_pct
except Exception:
    def battery_pct(): return None

class Home(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        box = BoxLayout(orientation='vertical', padding=16, spacing=12)
        box.add_widget(Label(text="Indoor Nav — Home", font_size=22))
        box.add_widget(Label(text="Start a demo route or adjust accessibility.", font_size=16))
        row = BoxLayout(size_hint=(1,0.15), spacing=12)
        btn = Button(text="Start Navigation"); btn.bind(on_release=lambda *_: self.start_nav())
        setbtn = Button(text="Settings"); setbtn.bind(on_release=lambda *_: setattr(self.manager,"current","settings"))
        row.add_widget(btn); row.add_widget(setbtn)
        box.add_widget(row); self.add_widget(box)
        p = battery_pct()
        if p is not None: log("battery_start_pct","",p)

    def start_nav(self):
        from kivy.app import App
        app = App.get_running_app()
        app.nav_t0 = time.perf_counter()  # 记录点击时刻
        log("click_start_nav")
        self.manager.current = "nav"

class Settings(Screen):
    def __init__(self, app, **kw):
        super().__init__(**kw); self.app = app
        b = BoxLayout(orientation='vertical', padding=16, spacing=10)
        b.add_widget(Label(text="Accessibility Settings", font_size=22))

        b.add_widget(Label(text="Persona"))
        persona = Spinner(text=self.app.settings["persona"], values=["blind","low-vision"])
        persona.bind(text=lambda _,v: self.set_and_log("persona",v)); b.add_widget(persona)

        b.add_widget(Label(text="Contrast"))
        hc = ToggleButton(text="High Contrast", state='down' if self.app.settings["contrast"]=="high" else 'normal')
        hc.bind(on_release=lambda w: self.set_and_log("contrast","high" if w.state=='down' else "normal")); b.add_widget(hc)

        b.add_widget(Label(text="Text Size"))
        big = ToggleButton(text="Large Text", state='down' if self.app.settings["textscale"]=="large" else 'normal')
        big.bind(on_release=lambda w: self.set_and_log("textscale","large" if w.state=='down' else "normal")); b.add_widget(big)

        b.add_widget(Label(text="Haptic Strength"))
        sp = Spinner(text=self.app.settings["haptic_strength"], values=["light","normal","strong"])
        sp.bind(text=lambda _,v: self.set_and_log("haptic_strength",v)); b.add_widget(sp)

        pre = Button(text="Run TTS Prewarm Benchmark"); pre.bind(on_release=lambda *_: self.run_prewarm()); b.add_widget(pre)

        back = Button(text="Back"); back.bind(on_release=lambda *_: setattr(self.manager,"current","home"))
        b.add_widget(back); self.add_widget(b)

    def set_and_log(self, k, v):
        self.app.settings[k] = v; log(f"settings_{k}", "", v)

    def run_prewarm(self):
        ms = prewarm("tts_prewarm_ms")
        log("tts_prewarm_ms","",ms)

class Navigate(Screen):
    def __init__(self, app, route_steps, **kw):
        super().__init__(**kw); self.app = app
        self.vm = NavViewModel(route_steps, app.settings)

        scale = 1.3 if app.settings["textscale"]=="large" else 1.0
        self.box = BoxLayout(orientation='vertical', padding=16, spacing=12)
        self.title = Label(text="Navigate", font_size=int(22*scale))
        self.info  = Label(text=f"Step 0/{len(self.vm.steps)}", font_size=int(16*scale))
        self.step  = Label(text="Press 'Next Instruction' to begin.", font_size=int(18*scale))
        row = BoxLayout(size_hint=(1,0.15), spacing=12)
        btnn=Button(text="Next Instruction"); btnr=Button(text="Simulate Reroute")
        btnn.bind(on_release=lambda *_: self.on_next()); btnr.bind(on_release=lambda *_: self.on_reroute())
        row.add_widget(btnn); row.add_widget(btnr)
        self.box.add_widget(self.title); self.box.add_widget(self.info); self.box.add_widget(self.step); self.box.add_widget(row)
        self.add_widget(self.box)

        log("warm_start_ms","",int((time.perf_counter()-APP_T0)*1000))

    def show_text(self,t): self.step.text=t
    def show_prog(self,i,n): self.info.text=f"Step {i}/{n}"

    def on_next(self):
        if self.vm.next_step(self.show_text, self.show_prog)=="arrived":
            self.manager.current="arrived"

    def on_reroute(self):
        self.vm.reroute(self.show_text,self.show_prog)

    def on_enter(self):
        from kivy.app import App
        app = App.get_running_app()
        if app.nav_t0 is not None:
            dt = int((time.perf_counter() - app.nav_t0) * 1000)
            log("warm_start_ms", "", dt)
            app.nav_t0 = None  # 重置，避免重复记

class Arrived(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        b=BoxLayout(orientation='vertical', padding=16, spacing=12)
        b.add_widget(Label(text="Arrived", font_size=22))
        b.add_widget(Label(text="You have reached your destination.", font_size=18))
        back=Button(text="Back to Home"); back.bind(on_release=lambda *_: setattr(self.manager,"current","home"))
        b.add_widget(back); self.add_widget(b)
        log("arrived")
        p = battery_pct()
        if p is not None: log("battery_end_pct","",p)

class NavApp(App):
    def __init__(self, **kw):
        super().__init__(**kw); self.settings = DEFAULT_SETTINGS.copy()
        self.nav_t0 = None

    def build(self):
        log("cold_start_ms","",int((time.perf_counter()-APP_T0)*1000))
        sm=ScreenManager(transition=NoTransition())
        steps = RouteModel().steps
        sm.add_widget(Home(name="home"))
        sm.add_widget(Settings(self, name="settings"))
        sm.add_widget(Navigate(self, steps, name="nav"))
        sm.add_widget(Arrived(name="arrived"))
        return sm

if __name__ == "__main__":
    NavApp().run()
