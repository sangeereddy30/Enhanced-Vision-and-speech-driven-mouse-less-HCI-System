import speech_recognition as sr
import threading
from utils import actions
import time

class VoiceController:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_running = False
        self.current_command = "None"
        self.stop_listening_fn = None
        self.mic = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            # Setup in a background thread so it doesn't block Flask response or Gestures
            threading.Thread(target=self._setup_and_start_listening, daemon=True).start()

    def stop(self):
        self.is_running = False
        if self.stop_listening_fn is not None:
            # Tell background listener to stop
            self.stop_listening_fn(wait_for_stop=False)
            self.stop_listening_fn = None
        self.current_command = "None"
        print("[Voice] Stopped listening.")

    def _setup_and_start_listening(self):
        print("[Voice] Voice thread initializing...")
        try:
            self.mic = sr.Microphone()
            with self.mic as source:
                print("[Voice] Calibrating to ambient noise (2 seconds)...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                # Boost sensitivity to ensure we pick up commands easier 
                self.recognizer.dynamic_energy_ratio = 1.5 
                print(f"[Voice] Calibrated! Listening continuously in background...")

            # listen_in_background spawns its own thread and continuously calls the callback
            # This is vastly superior/stable compared to a manual while loop!
            self.stop_listening_fn = self.recognizer.listen_in_background(
                self.mic, 
                self._audio_callback,
                phrase_time_limit=4
            )
        except Exception as e:
            print(f"[Voice] Critical Microphone Error: {e}. Check if microphone is plugged in/accessible.")

    def _audio_callback(self, recognizer, audio):
        if not self.is_running:
            return
            
        try:
            # Process strictly in the background without blocking the listen buffer
            command = recognizer.recognize_google(audio).lower()
            print(f"[Voice] Recognized Command: '{command}'")
            
            self.current_command = command
            self._execute_command(command)
        except sr.UnknownValueError:
            # Often triggered when breathing into mic or typing heavily
            print("[Voice] Could not understand audio.")
        except sr.RequestError as e:
            print(f"[Voice] API Error (Check Internet connection): {e}")
        except Exception as e:
            print(f"[Voice] Callback error: {e}")

    def _execute_command(self, command):
        # We perform robust substring matching to catch sentences like "can you right click"
        if "right" in command and "click" in command:
            actions.right_click()
        elif "click" in command:
            # Prevent conflict with right click
            if "right" not in command:
                actions.left_click()
        elif "scroll up" in command:
            actions.scroll_up()
        elif "scroll down" in command:
            actions.scroll_down()
        elif "open chrome" in command or "open browser" in command or "browser" in command:
            actions.open_chrome()
        elif "shutdown" in command:
            actions.shutdown()
        
        # Reset current command visual indicator dynamically
        threading.Timer(3.0, self._reset_command).start()
        
    def _reset_command(self):
        if self.is_running:
            self.current_command = "None"
