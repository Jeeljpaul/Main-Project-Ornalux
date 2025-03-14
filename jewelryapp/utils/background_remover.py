from rembg import remove
from PIL import Image
import io
import os
from django.conf import settings
import uuid
import logging

class BackgroundRemover:
    @staticmethod
    async def remove_background(image_path):
        try:
            # Set up logging
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(__name__)

            # Log image path and check if file exists
            logger.info(f"Processing image: {image_path}")
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None

            # Open and analyze input image
            input_image = Image.open(image_path)
            logger.info(f"Input image details:")
            logger.info(f"- Format: {input_image.format}")
            logger.info(f"- Size: {input_image.size}")
            logger.info(f"- Mode: {input_image.mode}")

            # Remove background
            logger.info("Removing background...")
            output_image = remove(input_image)
            
            logger.info(f"Output image details:")
            logger.info(f"- Size: {output_image.size}")
            logger.info(f"- Mode: {output_image.mode}")

            # Create a unique filename
            filename = f"no_bg_{uuid.uuid4().hex}.png"
            output_path = os.path.join(settings.MEDIA_ROOT, 'processed_images', filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the processed image
            output_image.save(output_path, 'PNG')
            logger.info(f"Saved processed image to: {output_path}")
            
            # Return the relative path
            return os.path.join('processed_images', filename)
            
        except Exception as e:
            logger.error(f"Error removing background: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
