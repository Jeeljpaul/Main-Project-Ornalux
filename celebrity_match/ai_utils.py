import torch
import cv2
import numpy as np
from ultralytics import YOLO
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input
from tensorflow.keras.models import Model
from django.conf import settings
from .models import Jewelry
from tensorflow.keras.preprocessing import image
from PIL import Image
import io
import os
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Load pre-trained YOLOv8 model (for object detection)
yolo_model = YOLO("yolov8n.pt")

# Load EfficientNetB0 (for feature extraction)
base_model = EfficientNetB0(weights="imagenet", include_top=False, pooling="avg")
feature_extractor = Model(inputs=base_model.input, outputs=base_model.output)

class JewelryMatcher:
    def __init__(self):
        self.yolo_model = YOLO('yolov8n.pt')
        self.efficient_net = EfficientNetB0(weights='imagenet', include_top=False, pooling='avg')
        
        # Expanded COCO classes for possible jewelry and accessories
        self.jewelry_classes = {
            1: 'person',      # People wearing jewelry
            24: 'backpack',   # Some jewelry bags might be detected as backpacks
            26: 'handbag',    # Jewelry pouches
            27: 'tie',        # Necklaces might be detected as ties
            31: 'handbag',    # Some jewelry might be detected as accessories
            32: 'tie',        # Necklaces or pendants
            37: 'sports ball', # Round jewelry
            39: 'bottle',     # Some pendants might be detected as bottles
            41: 'cup',        # Round jewelry
            76: 'scissors',   # Earrings
            77: 'teddy bear', # Fuzzy/textured items
            88: 'teddy bear', # Fuzzy/textured items
        }
        
    def detect_jewelry(self, image_path):
        """Detect objects in image using YOLOv8"""
        try:
            # Process the entire image as one detection
            # This helps when standard object detection fails
            img_array = np.array(image_path)
            height, width = img_array.shape[:2]
            
            # Create one detection for the entire image
            whole_image_detection = [{
                'bbox': (0, 0, width, height),
                'class': -1,  # Custom class for whole image
                'confidence': 1.0
            }]
            
            # Also run standard detection
            results = self.yolo_model(image_path)
            standard_detections = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0].cpu().numpy())
                    confidence = float(box.conf[0].cpu().numpy())
                    
                    logger.info(f"Detected object class {class_id} with confidence {confidence}")
                    
                    # Accept any object with reasonable confidence
                    if confidence > 0.2:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        # Expand the detection box slightly
                        height = y2 - y1
                        width = x2 - x1
                        x1 = max(0, x1 - width * 0.1)
                        x2 = x2 + width * 0.1
                        y1 = max(0, y1 - height * 0.1)
                        y2 = y2 + height * 0.1
                        
                        standard_detections.append({
                            'bbox': (x1, y1, x2, y2),
                            'class': class_id,
                            'confidence': confidence
                        })
            
            # Combine both approaches
            all_detections = whole_image_detection + standard_detections
            logger.info(f"Total detections: {len(all_detections)}")
            return all_detections
            
        except Exception as e:
            logger.error(f"Error in detect_jewelry: {str(e)}")
            return []
    
    def extract_features(self, img):
        """Extract features using EfficientNetB0"""
        try:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize image
            img = img.resize((224, 224))
            x = image.img_to_array(img)
            x = np.expand_dims(x, axis=0)
            
            # Preprocess input
            x = preprocess_input(x)
            
            features = self.efficient_net.predict(x)
            return features.flatten()
            
        except Exception as e:
            logger.error(f"Error in extract_features: {str(e)}")
            return None
    
    def find_similar_items(self, detected_jewelry, store_items, top_k=5):
        """Find similar jewelry items from store inventory"""
        try:
            detected_features = self.extract_features(detected_jewelry)
            if detected_features is None:
                return []

            similarities = []
            for item in store_items:
                try:
                    # Try to get cached features first
                    cache_key = f'product_features_{item.product_id}'
                    cached_features = cache.get(cache_key)
                    
                    if cached_features:
                        # Convert bytes back to numpy array
                        item_features = np.frombuffer(cached_features, dtype=np.float32)
                    else:
                        # If not cached, extract features and cache them
                        if not item.images:
                            continue
                            
                        item_img = Image.open(item.images.path)
                        if item_img.mode != 'RGB':
                            item_img = item_img.convert('RGB')
                            
                        item_features = self.extract_features(item_img)
                        
                        # Cache the features
                        if item_features is not None:
                            cache.set(cache_key, item_features.tobytes(), timeout=86400)  # Cache for 24 hours
                    
                    if item_features is not None:
                        # Ensure shapes match
                        if len(item_features) != len(detected_features):
                            logger.warning(f"Feature shape mismatch: {len(item_features)} vs {len(detected_features)}")
                            continue
                            
                        similarity = np.dot(detected_features, item_features) / (
                            np.linalg.norm(detected_features) * np.linalg.norm(item_features)
                        )
                        
                        # Very lenient matching for testing
                        if similarity > 0.05:
                            similarities.append((item, similarity))
                            logger.info(f"Similarity score for item {item.product_id}: {similarity}")
                except Exception as e:
                    logger.error(f"Error processing store item {item.product_id}: {str(e)}")
                    continue

            # Sort by similarity and return top_k matches
            similarities.sort(key=lambda x: x[1], reverse=True)
            return [item for item, _ in similarities[:top_k]]
            
        except Exception as e:
            logger.error(f"Error in find_similar_items: {str(e)}")
            return []

def match_jewelry(detected_jewelry):
    """
    Matches detected jewelry to the most similar item in the store.
    """
    store_jewelry = Jewelry.objects.all()
    store_features = np.array([np.fromstring(j.features, sep=",") for j in store_jewelry])

    best_matches = []
    for jewelry_img in detected_jewelry:
        query_features = extract_features(jewelry_img)
        similarities = np.dot(store_features, query_features)  # Cosine similarity
        best_match_index = np.argmax(similarities)
        best_matches.append(store_jewelry[best_match_index])

    return best_matches
