# Add these imports at the top
import tensorflow as tf
import numpy as np
import cv2
import os

# Get the model path relative to this file
model_path = os.path.join(os.path.dirname(__file__), "trained_model.keras")

# Load trained model with proper error handling
try:
    # Custom objects dict for loading the model
    custom_objects = {
        'MeanSquaredError': tf.keras.losses.MeanSquaredError,
        'MeanAbsoluteError': tf.keras.metrics.MeanAbsoluteError
    }
    
    model = tf.keras.models.load_model(
        model_path,
        custom_objects=custom_objects
    )
except:
    # If model doesn't exist, create a dummy model
    from train_model import create_dummy_model
    create_dummy_model()
    model = tf.keras.models.load_model(
        model_path,
        custom_objects=custom_objects
    )

# Start webcam capture
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    try:
        # Preprocess image
        img = cv2.resize(frame, (224, 224))
        img = img / 255.0
        img = np.expand_dims(img, axis=0)

        # Predict hand keypoints
        keypoints = model.predict(img)[0].reshape(-1, 3)  # Reshape to 21 points

        # Draw keypoints on frame
        for (x, y, z) in keypoints:
            x, y = int(x * frame.shape[1]), int(y * frame.shape[0])
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

        cv2.imshow("Hand Pose Estimation", frame)

    except Exception as e:
        print(f"Error processing frame: {str(e)}")

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
