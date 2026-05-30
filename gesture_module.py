import cv2
import mediapipe as mp
import pyautogui
import threading
import math
import numpy as np
import time

class GestureController:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.is_running = False
        self.current_gesture = "None"
        self.cap = None
        self.frame = None
        self.screen_w, self.screen_h = pyautogui.size()
        
        # Disable pyautogui fail-safe to avoid throwing exceptions strictly at edges
        pyautogui.FAILSAFE = False 
        
        # Smoothing setup for stable cursor
        self.prev_x, self.prev_y = 0, 0
        self.smooth_factor = 0.5 

    def start(self):
        print("🔥 START endpoint hit")

        if not self.is_running:
            print("Starting camera...")
            self.is_running = True
            
            self.cap = cv2.VideoCapture(0)

            if not self.cap.isOpened():
                print("❌ Camera failed with index 0, trying DirectShow...")
                self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

            if not self.cap.isOpened():
                print("❌ Camera STILL not opening!")
            else:
                print("✅ Camera opened successfully")

            self.thread = threading.Thread(target=self._process_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.frame = None
        self.current_gesture = "None"

    def generate_frames(self):
        # Create a default 'Initializing' frame to prevent broken image payload in browser 
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(blank_frame, "Initializing Camera...", (130, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        _, blank_buffer = cv2.imencode('.jpg', blank_frame)
        blank_bytes = blank_buffer.tobytes()

        while True:
            if not self.is_running or self.frame is None:
                # Yield valid blank JPEG payload instead of empty bytes
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + blank_bytes + b'\r\n')
                time.sleep(0.1)
                continue
            
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', self.frame)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    def _process_loop(self):
        while self.is_running and self.cap is not None and self.cap.isOpened():
            success, img = self.cap.read()
            if not success:
                continue

            # Mirror image for intuitive control
            img = cv2.flip(img, 1) 
            h, w, c = img.shape
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Process hands using MediaPipe
            results = self.hands.process(img_rgb)
            face_results = self.face_mesh.process(img_rgb)
            
            gesture = "None"
            moved_by_hand = False

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw landmarks on image
                    self.mp_draw.draw_landmarks(img, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    # Extract list of coordinates
                    lm_list = []
                    for id, lm in enumerate(hand_landmarks.landmark):
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        lm_list.append((id, cx, cy))
                    
                    if len(lm_list) > 20: 
                        thumb_tip = lm_list[4]
                        index_tip = lm_list[8]
                        
                        fingers = self._fingers_up(lm_list)
                        
                        # 1. Fist -> Stop movement (all fingers down)
                        if fingers.count(1) == 0:
                            gesture = "Fist (Stop)"
                            moved_by_hand = True
                        elif fingers[1] == 1 and fingers[2] == 0:
                            # Distance between index and thumb
                            length = math.hypot(index_tip[1] - thumb_tip[1], index_tip[2] - thumb_tip[2])
                            
                            if length < 40:
                                gesture = "Pinch (Left Click)"
                                cv2.circle(img, (index_tip[1], index_tip[2]), 15, (0, 255, 0), cv2.FILLED)
                                pyautogui.click()
                                cv2.waitKey(250) # Cooldown to prevent multiple quick clicks
                                moved_by_hand = True
                            else:
                                gesture = "Index Pointing (Move)"
                                moved_by_hand = True
                                # Bounding box so users don't have to reach screen edges literally in camera
                                box_margin = 100
                                cv2.rectangle(img, (box_margin, box_margin), (w - box_margin, h - box_margin), (255, 0, 255), 2)
                                
                                # Interpolate coordinates
                                x3 = np.interp(index_tip[1], (box_margin, w - box_margin), (0, self.screen_w))
                                y3 = np.interp(index_tip[2], (box_margin, h - box_margin), (0, self.screen_h))
                                
                                # Smooth values
                                curr_x = self.prev_x + (x3 - self.prev_x) * self.smooth_factor
                                curr_y = self.prev_y + (y3 - self.prev_y) * self.smooth_factor
                                
                                try:
                                    pyautogui.moveTo(curr_x, curr_y)
                                except Exception:
                                    pass
                                    
                                self.prev_x, self.prev_y = curr_x, curr_y

                        # 3. Two fingers -> Scroll
                        elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0:
                            moved_by_hand = True
                            if index_tip[2] < h//2 - 40:
                                pyautogui.scroll(120)
                                gesture = "Two Fingers (Scroll Up)"
                            elif index_tip[2] > h//2 + 40:
                                pyautogui.scroll(-120)
                                gesture = "Two Fingers (Scroll Down)"
                            else:
                                gesture = "Two Fingers (Hover/Ready to Scroll)"

            # 4. Head Movement Data (Fallback if hand is not moving)
            if not moved_by_hand and face_results.multi_face_landmarks:
                for face_landmarks in face_results.multi_face_landmarks:
                    # Get nose tip landmark (index 1 is standard for nose tip in mediapipe)
                    nose_tip = face_landmarks.landmark[1]
                    cx, cy = int(nose_tip.x * w), int(nose_tip.y * h)
                    
                    gesture = "Head (Move)"
                    box_margin = 100
                    cv2.rectangle(img, (box_margin, box_margin), (w - box_margin, h - box_margin), (255, 255, 0), 2)
                    cv2.circle(img, (cx, cy), 10, (0, 0, 255), cv2.FILLED)
                    
                    # Interpolate coordinates
                    x3 = np.interp(cx, (box_margin, w - box_margin), (0, self.screen_w))
                    y3 = np.interp(cy, (box_margin, h - box_margin), (0, self.screen_h))
                    
                    # Smooth values
                    curr_x = self.prev_x + (x3 - self.prev_x) * self.smooth_factor
                    curr_y = self.prev_y + (y3 - self.prev_y) * self.smooth_factor
                    
                    try:
                        pyautogui.moveTo(curr_x, curr_y)
                    except Exception:
                        pass
                        
                    self.prev_x, self.prev_y = curr_x, curr_y
                    break

            self.current_gesture = gesture
            self.frame = img

    def _fingers_up(self, lm_list):
        fingers = []
        tipIds = [4, 8, 12, 16, 20]
        
        # Thumb: Simple logic - compare x bounds
        if lm_list[tipIds[0]][1] < lm_list[tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)
            
        # 4 Fingers: Check y coords
        for id in range(1, 5):
            if lm_list[tipIds[id]][2] < lm_list[tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
                
        return fingers
