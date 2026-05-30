from flask import Flask, render_template, Response, jsonify
import threading
from gesture_module import GestureController
from voice_module import VoiceController
import logging

app = Flask(__name__)
# Suppress standard flask logging for a cleaner terminal output
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

gesture_controller = GestureController()
voice_controller = VoiceController()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gesture_controller.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    return jsonify({
        'gesture': gesture_controller.current_gesture,
        'voice': voice_controller.current_command,
        'is_running': gesture_controller.is_running and voice_controller.is_running
    })

@app.route('/start')
def start():
    print("Starting HCI Modules...")
    gesture_controller.start()
    voice_controller.start()
    return jsonify({'status': 'Started'})

@app.route('/stop')
def stop():
    print("Stopping HCI Modules...")
    gesture_controller.stop()
    voice_controller.stop()
    return jsonify({'status': 'Stopped'})

if __name__ == '__main__':
    print("=========================================================")
    print(" Enhanced Vision and Speech-Driven Mouse-Less HCI System ")
    print("=========================================================")
    print("Server running! Navigate to http://127.0.0.1:5000")
    app.run(debug=True, threaded=True, use_reloader=False)
