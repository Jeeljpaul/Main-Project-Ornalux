import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.efficientnet import preprocess_input
import numpy as np
import os
from django.conf import settings
import glob

def load_model():
    # Load EfficientNetB0 model
    base_model = EfficientNetB0(weights='imagenet', include_top=False, pooling='avg')
    return base_model

def extract_features(img_path, model):
    # Load and preprocess the image
    img = image.load_img(img_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    
    # Extract features
    features = model.predict(x)
    return features

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def recommend_jewelry(dress_image_path, num_recommendations=5):
    try:
        # Load the model
        model = load_model()
        
        # Extract features from the uploaded dress image
        dress_features = extract_features(dress_image_path, model)
        
        # Path to directory containing jewelry images
        jewelry_dir = os.path.join(settings.MEDIA_ROOT, 'jewelry_samples')
        os.makedirs(jewelry_dir, exist_ok=True)  # Create directory if it doesn't exist
        
        # Find all image files in the jewelry directory
        image_extensions = ['jpg', 'jpeg', 'png']
        jewelry_images = []
        
        for ext in image_extensions:
            jewelry_images.extend(glob.glob(os.path.join(jewelry_dir, f'*.{ext}')))
        
        recommendations = []
        
        # Compare with each jewelry item
        for jewelry_image_path in jewelry_images:
            try:
                # Extract features for jewelry image
                jewelry_features = extract_features(jewelry_image_path, model)
                
                # Calculate similarity
                similarity = cosine_similarity(dress_features.flatten(), jewelry_features.flatten())
                
                # Get jewelry name from filename
                jewelry_name = os.path.basename(jewelry_image_path).split('.')[0].replace('_', ' ').title()
                
                # Create relative URL path for the image
                image_rel_path = os.path.relpath(jewelry_image_path, settings.MEDIA_ROOT)
                image_url = os.path.join(settings.MEDIA_URL, image_rel_path)
                
                recommendations.append({
                    'name': jewelry_name,
                    'image_url': image_url,
                    'similarity': float(similarity)
                })
            except Exception as e:
                print(f"Error processing image {jewelry_image_path}: {str(e)}")
                continue
        
        # Sort by similarity and get top recommendations
        recommendations.sort(key=lambda x: x['similarity'], reverse=True)
        recommendations = recommendations[:num_recommendations]
        
        # Clean up the uploaded image
        if os.path.exists(dress_image_path):
            os.remove(dress_image_path)
            
        return [(r['name'], r['image_url'], r['similarity']) for r in recommendations]
        
    except Exception as e:
        print(f"Error in recommendation system: {str(e)}")
        return []
