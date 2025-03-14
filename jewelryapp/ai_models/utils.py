import tensorflow as tf
import numpy as np
import cv2
import os
import logging
import mediapipe as mp
from functools import partial
import threading
import queue

# Initialize logger and MediaPipe
logger = logging.getLogger(__name__)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=1,
    min_detection_confidence=0.5
)

def load_model():
    """Load the trained model with proper error handling"""
    try:
        model_path = os.path.join(os.path.dirname(__file__), "trained_model.keras")
        
        # Define custom objects for model loading
        custom_objects = {
            'MeanSquaredError': tf.keras.losses.MeanSquaredError,
            'MeanAbsoluteError': tf.keras.metrics.MeanAbsoluteError
        }
        
        if not os.path.exists(model_path):
            logger.error(f"Model file not found at {model_path}")
            # Create and save a dummy model if the real one doesn't exist
            from .train_model import create_and_train_model
            model = create_and_train_model()
            if model is None:
                raise Exception("Failed to create dummy model")
            logger.info("Created dummy model for testing")
            return model
        
        return tf.keras.models.load_model(model_path, custom_objects=custom_objects)
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return None

# Load the model
model = load_model()
print(f"Model loaded successfully: {model is not None}")

if model is None:
    print("Warning: Failed to load model, creating dummy model...")
    from .train_model import create_and_train_model
    model = create_and_train_model()
    print(f"Dummy model created and loaded: {model is not None}")

# Ring size mapping - using Indian sizes
ring_sizes = {
    "Indian 1": 45.0, "Indian 2": 45.7, "Indian 3": 46.4,
    "Indian 4": 47.1, "Indian 5": 47.8, "Indian 6": 48.5,
    "Indian 7": 49.2, "Indian 8": 49.9, "Indian 9": 50.6,
    "Indian 10": 51.3, "Indian 11": 52.0, "Indian 12": 52.7,
    "Indian 13": 53.4, "Indian 14": 54.1, "Indian 15": 54.8,
    "Indian 16": 55.5, "Indian 17": 56.2, "Indian 18": 56.9,
    "Indian 19": 57.6, "Indian 20": 58.3, "Indian 21": 59.0,
    "Indian 22": 59.7, "Indian 23": 60.4, "Indian 24": 61.1,
    "Indian 25": 61.8, "Indian 26": 62.5, "Indian 27": 63.2,
    "Indian 28": 63.9, "Indian 29": 64.6, "Indian 30": 65.3
}

def detect_hand(image):
    """Detect if a hand is present in the image and return hand landmarks"""
    try:
        # Convert the image to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect hands
        results = hands.process(image_rgb)
        
        if not results.multi_hand_landmarks:
            return False, None
        
        return True, results.multi_hand_landmarks[0]
    except Exception as e:
        logger.error(f"Error in hand detection: {str(e)}")
        return False, None

def calculate_finger_length(landmarks, image_shape):
    """Calculate ring finger length from landmarks"""
    try:
        # MediaPipe hand landmarks for ring finger
        RING_FINGER_MCP = 13  # Base of ring finger
        RING_FINGER_PIP = 14  # First joint
        RING_FINGER_DIP = 15  # Second joint
        RING_FINGER_TIP = 16  # Tip
        WRIST = 0            # Wrist landmark for scaling

        # Get all required landmarks
        mcp = landmarks.landmark[RING_FINGER_MCP]
        pip = landmarks.landmark[RING_FINGER_PIP]
        dip = landmarks.landmark[RING_FINGER_DIP]
        tip = landmarks.landmark[RING_FINGER_TIP]
        wrist = landmarks.landmark[WRIST]

        # Convert to pixel coordinates
        def to_pixel(point):
            return np.array([point.x * image_shape[1], point.y * image_shape[0], point.z * image_shape[1]])

        mcp_px = to_pixel(mcp)
        pip_px = to_pixel(pip)
        dip_px = to_pixel(dip)
        tip_px = to_pixel(tip)
        wrist_px = to_pixel(wrist)

        # Calculate hand size for scaling (wrist to middle finger MCP)
        hand_scale = np.linalg.norm(wrist_px - mcp_px)
        
        # Calculate circumference using segments
        segment1 = np.linalg.norm(mcp_px - pip_px)
        segment2 = np.linalg.norm(pip_px - dip_px)
        segment3 = np.linalg.norm(dip_px - tip_px)
        
        # Total length in pixels
        total_length_px = segment1 + segment2 + segment3
        
        # Improved calibration factors
        CALIBRATION_FACTOR = 58  # average ring finger circumference
        CORRECTION_FACTORS = {
            'small': 0.82,   # For measurements < 50mm
            'medium': 0.85,  # For measurements 50-60mm
            'large': 0.87    # For measurements > 60mm
        }
        
        # Calculate base measurement
        mm_per_pixel = CALIBRATION_FACTOR / hand_scale
        circumference_mm = total_length_px * mm_per_pixel
        
        # Apply dynamic correction factor
        if circumference_mm < 50:
            correction = CORRECTION_FACTORS['small']
        elif circumference_mm > 60:
            correction = CORRECTION_FACTORS['large']
        else:
            correction = CORRECTION_FACTORS['medium']
            
        final_measurement = circumference_mm * correction
        
        # Round to nearest 0.5mm for stability
        final_measurement = round(final_measurement * 2) / 2
        
        logger.info(f"Raw: {circumference_mm:.1f}mm, Corrected: {final_measurement:.1f}mm")
        return final_measurement
        
    except Exception as e:
        logger.error(f"Error calculating finger length: {str(e)}")
        raise

def predict_ring_size(image_path, timeout=5):
    """Predict ring size from an image"""
    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            logger.error("Failed to load image")
            return "Failed to load image", None, None
        
        # Detect hand
        hand_present, landmarks = detect_hand(img)
        
        if not hand_present:
            logger.info("No hand detected in image")
            return "No hand detected. Please show your hand clearly.", None, None
        
        try:
            # Calculate ring finger circumference
            circumference_mm = calculate_finger_length(landmarks, img.shape)
            
            # Validate measurement range (typical ring sizes range from 45-70mm)
            if circumference_mm < 45:
                return "Measurement too small. Please position your hand properly.", None, landmarks
            if circumference_mm > 70:
                return "Measurement too large. Please position your hand properly.", None, landmarks
            
            # Find closest ring size
            closest_size = min(ring_sizes.items(), 
                             key=lambda x: abs(x[1] - circumference_mm))[0]
            
            logger.info(f"Successful measurement: {circumference_mm:.1f}mm, size: {closest_size}")
            return closest_size, circumference_mm, landmarks
            
        except Exception as e:
            logger.error(f"Error in measurement calculation: {str(e)}")
            return "Error calculating measurement. Please try again.", None, None
            
    except Exception as e:
        logger.error(f"Error in ring size prediction: {str(e)}")
        return f"Error during prediction: {str(e)}", None, None
