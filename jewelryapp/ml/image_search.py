import tensorflow as tf
from tensorflow.keras.applications import ResNet50, VGG16, EfficientNetB0
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess
from tensorflow.keras.applications.vgg16 import preprocess_input as vgg_preprocess
from tensorflow.keras.applications.efficientnet import preprocess_input as efficient_preprocess
import numpy as np
import cv2
from PIL import Image
import io
from scipy.spatial.distance import cosine
from typing import List, Tuple
import logging

class JewelryImageSearch:
    def __init__(self):
        # Initialize multiple models for ensemble approach
        self.resnet_model = ResNet50(weights='imagenet', include_top=False, pooling='avg')
        self.vgg_model = VGG16(weights='imagenet', include_top=False, pooling='avg')
        self.efficient_model = EfficientNetB0(weights='imagenet', include_top=False, pooling='avg')
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Image preprocessing parameters
        self.target_size = (224, 224)
        self.brightness_range = (0.8, 1.2)
        
    def preprocess_image(self, img: Image.Image) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Preprocess image for all three models with jewelry-specific enhancements
        """
        # Convert PIL Image to OpenCV format
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # Enhance jewelry features
        img_cv = self._enhance_jewelry_features(img_cv)
        
        # Convert back to RGB
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        
        # Resize image
        img_resized = cv2.resize(img_rgb, self.target_size)
        
        # Prepare inputs for each model
        resnet_input = resnet_preprocess(np.copy(img_resized))
        vgg_input = vgg_preprocess(np.copy(img_resized))
        efficient_input = efficient_preprocess(np.copy(img_resized))
        
        return resnet_input, vgg_input, efficient_input
    
    def _enhance_jewelry_features(self, img: np.ndarray) -> np.ndarray:
        """
        Enhance jewelry-specific features using OpenCV
        """
        # Convert to LAB color space for better color processing
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        
        # Merge channels
        lab = cv2.merge((l,a,b))
        
        # Convert back to BGR
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Denoise
        enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
        
        return enhanced
    
    def extract_features(self, img: Image.Image) -> np.ndarray:
        """
        Extract features using ensemble of models
        """
        try:
            # Preprocess image for all models
            resnet_input, vgg_input, efficient_input = self.preprocess_image(img)
            
            # Extract features from each model
            resnet_features = self.resnet_model.predict(np.expand_dims(resnet_input, axis=0))
            vgg_features = self.vgg_model.predict(np.expand_dims(vgg_input, axis=0))
            efficient_features = self.efficient_model.predict(np.expand_dims(efficient_input, axis=0))
            
            # Concatenate features
            combined_features = np.concatenate([
                resnet_features.flatten(),
                vgg_features.flatten(),
                efficient_features.flatten()
            ])
            
            # Normalize features
            normalized_features = combined_features / np.linalg.norm(combined_features)
            
            return normalized_features
            
        except Exception as e:
            self.logger.error(f"Error extracting features: {str(e)}")
            raise
    
    def compute_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """
        Compute similarity between two feature vectors using weighted metrics
        """
        try:
            # Compute cosine similarity
            cosine_sim = 1 - cosine(features1, features2)
            
            # Compute euclidean similarity
            euclidean_dist = np.linalg.norm(features1 - features2)
            euclidean_sim = 1 / (1 + euclidean_dist)
            
            # Weighted combination
            similarity = 0.7 * cosine_sim + 0.3 * euclidean_sim
            
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Error computing similarity: {str(e)}")
            raise

# Create an instance of JewelryImageSearch at the module level
jewelry_search = JewelryImageSearch()

# Export the instance
__all__ = ['jewelry_search'] 