import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Ring size conversion function
def get_ring_size(finger_width_mm):
    # Approximate size chart (adjust as needed)
    ring_sizes = {
        "US 4": 14.8, "US 5": 15.6, "US 6": 16.4, "US 7": 17.3, 
        "US 8": 18.1, "US 9": 19.0, "US 10": 19.8, "US 11": 20.6
    }
    closest_size = min(ring_sizes, key=lambda size: abs(ring_sizes[size] - finger_width_mm))
    return closest_size

# Capture video from webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        continue
    
    # Convert image to RGB for MediaPipe
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Get x-coordinates of index finger base (PIP) and tip
            base = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP]
            tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]

            # Convert to pixel coordinates
            h, w, _ = frame.shape
            base_x, base_y = int(base.x * w), int(base.y * h)
            tip_x, tip_y = int(tip.x * w), int(tip.y * h)

            # Calculate pixel distance
            pixel_width = abs(base_x - tip_x)

            # Convert pixels to mm (approximate, assuming 1 pixel = 0.26mm at standard distance)
            finger_width_mm = pixel_width * 0.26  

            # Get ring size
            ring_size = get_ring_size(finger_width_mm)

            # Draw landmarks
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Display measurements
            cv2.putText(frame, f"Width: {finger_width_mm:.1f} mm", (base_x, base_y - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Ring Size: {ring_size}", (base_x, base_y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    # Show the frame
    cv2.imshow("Ring Size Detector", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
