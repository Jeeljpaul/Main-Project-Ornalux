import tensorflow as tf
import numpy as np
import cv2
import glob
import json
import os

def create_dummy_dataset():
    """Create a small dummy dataset for testing"""
    # Create dummy images (10 samples)
    X_train = np.random.rand(10, 224, 224, 3)  # RGB images
    X_test = np.random.rand(2, 224, 224, 3)
    
    # Create dummy keypoints (21 points with x,y,z coordinates)
    y_train = np.random.rand(10, 21, 3)  # 21 keypoints with 3D coordinates
    y_test = np.random.rand(2, 21, 3)
    
    # Reshape labels to match model output
    y_train = y_train.reshape(10, 63)  # Flatten to (batch_size, 21*3)
    y_test = y_test.reshape(2, 63)
    
    return X_train, y_train, X_test, y_test

def create_and_train_model():
    """Create and train the hand pose estimation model"""
    try:
        # Get dummy data
        X_train, y_train, X_test, y_test = create_dummy_dataset()
        
        # Create model
        model = tf.keras.Sequential([
            # Input layer
            tf.keras.layers.Input(shape=(224, 224, 3)),
            
            # Convolutional layers
            tf.keras.layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
            tf.keras.layers.MaxPooling2D(2, 2),
            tf.keras.layers.BatchNormalization(),
            
            tf.keras.layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
            tf.keras.layers.MaxPooling2D(2, 2),
            tf.keras.layers.BatchNormalization(),
            
            tf.keras.layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
            tf.keras.layers.MaxPooling2D(2, 2),
            tf.keras.layers.BatchNormalization(),
            
            # Flatten and Dense layers
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(512, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(63)  # Output: 21 keypoints * 3 coordinates
        ])
        
        # Compile model with proper loss function
        model.compile(
            optimizer='adam',
            loss=tf.keras.losses.MeanSquaredError(),  # Use the proper loss class
            metrics=[tf.keras.metrics.MeanAbsoluteError()]  # Use proper metrics class
        )
        
        # Train model
        print("Training model...")
        history = model.fit(
            X_train, y_train,
            epochs=5,  # Reduced epochs for testing
            batch_size=2,
            validation_data=(X_test, y_test),
            verbose=1
        )
        
        # Save model in the newer format
        model_path = os.path.join(os.path.dirname(__file__), "trained_model.keras")
        model.save(model_path, save_format='keras')
        print(f"Model saved to {model_path}")
        
        return model
        
    except Exception as e:
        print(f"Error during model creation/training: {str(e)}")
        return None

if __name__ == "__main__":
    # Create and train the model
    model = create_and_train_model()
    
    if model is not None:
        print("Model created and trained successfully!")
    else:
        print("Failed to create/train model")
