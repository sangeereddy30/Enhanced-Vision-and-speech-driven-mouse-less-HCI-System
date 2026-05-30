# Enhanced Vision and Speech-Driven Mouse-Less HCI System

A fully integrated multimodal interface allowing users to control their system using hands gestures (via webcam) and voice commands (via microphone). Designed to provide an accessible, touchless desktop experience.

## Prerequisites

- Python 3.8 to 3.11 (Required for PyAudio and SpeechRecognition)
- A working Webcam
- A working Microphone

## Setup Instructions

1. **Install Dependencies:**
   Open a terminal in the project directory and run:
   ```bash
   pip install -r requirements.txt
   ```

2. **Wait for installations:**
   *Note: If `pyaudio` fails to install on Windows due to missing C++ Build Tools, you may need to use `pipwin`:*
   ```bash
   pip install pipwin
   pipwin install pyaudio
   ```

3. **Run the Application locally:**
   ```bash
   python app.py
   ```

4. **Access the Dashboard:**
   Open your web browser and navigate to `http://127.0.0.1:5000`.
   Click on the **"Start System"** button to initialize the controllers. Keep your hand visible to the camera!

## Features and Commands

### Hand Gestures
- **Move Cursor:** Raise your index finger only.
- **Left Click:** Bring your index finger and thumb close together (Pinch). 
- **Scroll:** Keep index and middle fingers up. 
    - Move hands physically towards the top of the screen to trigger scroll up.
    - Move hands towards the bottom to trigger scroll down.
- **Stop Control:** Make a tight fist (all fingers closed). Mouse freezes.

### Voice Actions
- `"click"` - Left clicks the mouse.
- `"right click"` - Right clicks the mouse.
- `"scroll up"` - Scrolls the screen upwards.
- `"scroll down"` - Scrolls the screen downwards.
- `"open chrome"` / `"open browser"` - Opens the Google Chrome browser.
- `"shutdown"` - Triggers a delayed PC shutdown sequence (can be aborted via terminal `shutdown /a`).

## Example Test Cases
- **Test Case 1 (Pointer Movement):** From a medium distance to the webcam, raise your index finger and move it slowly; observe mouse tracking smoothly to the equivalent screen region without dropping out.
- **Test Case 2 (Clicking):** Hover over an icon and pinch your fingers tightly together; observe the system trigger a left click without stuttering.
- **Test Case 3 (Voice Browser):** Speak aloud "Open Chrome" clearly into the mic; observe the browser launching automatically.
- **Test Case 4 (Multimodal):** Move pointer to a text field using the index finger gesture, then say "click" to focus the element interactively! 
