from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib import messages
from .forms import CelebrityUploadForm
from .models import CelebrityUpload
from .ai_utils import JewelryMatcher
from PIL import Image
from jewelryapp.models import Product
import os
import logging
import time

logger = logging.getLogger(__name__)

def upload_celebrity_image(request):
    """
    Handles celebrity image upload and processes jewelry detection.
    """
    if request.method == "POST":
        form = CelebrityUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save()
            image_path = os.path.join("media", str(upload.image))
            
            # Detect jewelry
            detected_jewelry = detect_jewelry(image_path)

            # Match with store jewelry
            matches = match_jewelry(detected_jewelry)

            return render(request, "celebrity_match/results.html", {"matches": matches})
    else:
        form = CelebrityUploadForm()
    
    return render(request, "celebrity_match/upload.html", {"form": form})

def upload_image(request):
    if request.method == 'POST':
        form = CelebrityUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Get the uploaded image
                image_file = request.FILES['image']
                img = Image.open(image_file)
                
                # Log image details
                logger.info(f"Uploaded image size: {img.size}, mode: {img.mode}")
                
                # Initialize matcher
                matcher = JewelryMatcher()
                
                # Detect jewelry in the image
                detections = matcher.detect_jewelry(img)
                logger.info(f"Found {len(detections)} detections")
                
                # Get all products with images
                store_items = Product.objects.filter(
                    images__isnull=False,  # Make sure image field is not null
                    is_active=True  # Only get active products
                ).distinct()
                
                logger.info(f"Found {store_items.count()} products with images in database")
                
                all_matches = []
                # For each detected region
                for idx, detection in enumerate(detections):
                    try:
                        # Crop the detected region
                        x1, y1, x2, y2 = detection['bbox']
                        jewelry_crop = img.crop((int(x1), int(y1), int(x2), int(y2)))
                        
                        # Find similar items
                        similar_items = matcher.find_similar_items(jewelry_crop, store_items, top_k=3)
                        logger.info(f"Detection {idx}: Found {len(similar_items)} similar items")
                        
                        all_matches.extend(similar_items)
                    except Exception as e:
                        logger.error(f"Error processing detection {idx}: {str(e)}")
                        continue
                
                # Remove duplicates while preserving order
                seen = set()
                matches = []
                for match in all_matches:
                    if match.product_id not in seen:
                        seen.add(match.product_id)
                        matches.append(match)
                
                if not matches:
                    messages.warning(request, "No matching jewelry items found. Try uploading a clearer image with visible jewelry.")
                else:
                    messages.success(request, f"Found {len(matches)} matching items!")
                
                # Prepare data for template
                match_data = []
                for match in matches:
                    match_data.append({
                        'name': match.product_name,
                        'image': match.images,
                        'category': match.category.name if match.category else "Uncategorized",
                        'price': match.price,
                        'get_absolute_url': f"/product/{match.product_id}/"
                    })
                
                return render(request, 'celebrity_match/results.html', {
                    'matches': match_data,
                    'detection_count': len(detections)
                })
                
            except Exception as e:
                logger.error(f"Error processing image: {str(e)}")
                messages.error(request, f"Error processing the image: {str(e)}")
                return render(request, 'celebrity_match/upload.html', {'form': form})
    else:
        form = CelebrityUploadForm()
    
    return render(request, 'celebrity_match/upload.html', {'form': form})
