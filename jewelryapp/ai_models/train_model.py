import tensorflow as tf
import os

def create_dummy_model():
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(224, 224, 3)),
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(63)  # 21 keypoints * 3 coordinates
    ])
    
    model.compile(optimizer='adam', loss='mse')
    
    # Save the model
    model_path = os.path.join(os.path.dirname(__file__), "trained_model.h5")
    model.save(model_path)
    print(f"Dummy model saved to {model_path}")

if __name__ == "__main__":
    create_dummy_model() 