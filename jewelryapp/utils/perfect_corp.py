from django.conf import settings
import requests
from PIL import Image
import io
import base64
import asyncio
import os

class PerfectCorpSDK:
    def __init__(self):
        self.api_key = settings.PERFECT_CORP_API_KEY
        self.base_url = "https://api.perfectcorp.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })

    async def process_single_image_to_3d(self, product, processed_image_path=None):
        """Convert single product image to 3D model using Perfect Corp's single-view technology"""
        try:
            # Use processed image if available, otherwise use main image
            if processed_image_path:
                main_image = await self._prepare_processed_image(processed_image_path)
            else:
                main_image = await self._prepare_main_image(product)

            if not main_image:
                raise ValueError("No valid image available for processing")

            # Get additional images if available
            additional_images = await self._get_additional_images(product)

            # Get product type and tracking mode
            product_type = self._determine_product_type(product.category.name)
            tracking_mode = self._get_tracking_mode(product_type)

            # Prepare conversion payload with Single-View optimizations
            payload = {
                "productType": product_type,
                "mainImage": main_image,
                "additionalImages": additional_images,
                "settings": {
                    "quality": "high",
                    "generateFromSingleView": True,
                    "enhanceDetails": True,
                    "autoCorrectLighting": True,
                    "optimizeMesh": True,
                    "textureResolution": 2048,
                    "geometryComplexity": "high"
                },
                "tracking": {
                    "mode": tracking_mode,
                    "enhancedTracking": True
                },
                "metadata": {
                    "productName": product.product_name,
                    "category": product.category.name,
                    "material": product.metaltype.name if product.metaltype else "Unknown"
                }
            }

            # Initialize conversion
            conversion_id = await self._start_conversion(payload)
            
            # Wait for and return results with enhanced data
            model_data = await self._get_conversion_results(conversion_id)
            
            return {
                "modelData": model_data,
                "renderSettings": {
                    "lighting": "STUDIO",
                    "background": "transparent",
                    "shadows": True,
                    "reflection": True,
                    "trackingMode": tracking_mode,
                    "materialProperties": self._get_material_properties(product)
                }
            }

        except Exception as e:
            print(f"Error in 3D conversion: {str(e)}")
            raise

    async def _prepare_main_image(self, product):
        """Prepare the main product image for conversion"""
        if not product.images:
            return None

        try:
            # Open and process the main image
            img = Image.open(product.images.path)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Optimize image size (Perfect Corp recommends between 1024px and 2048px)
            target_size = 1024
            if img.width < target_size or img.height < target_size:
                ratio = target_size / min(img.width, img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)

            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=95)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')

        except Exception as e:
            print(f"Error preparing main image: {str(e)}")
            return None

    async def _get_additional_images(self, product):
        """Get additional product images if available"""
        additional_images = []
        
        for img_field in ['image2', 'image3', 'image4']:
            if hasattr(product, img_field) and getattr(product, img_field):
                try:
                    img = Image.open(getattr(product, img_field).path)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=95)
                    additional_images.append(
                        base64.b64encode(buffer.getvalue()).decode('utf-8')
                    )
                except Exception as e:
                    print(f"Error processing {img_field}: {str(e)}")
                    continue

        return additional_images

    def _determine_product_type(self, category_name):
        """Map category name to Perfect Corp product type"""
        category_mapping = {
            'Rings': 'RING',
            'Necklaces': 'NECKLACE',
            'Earrings': 'EARRING',
            'Bracelets': 'BRACELET'
        }
        return category_mapping.get(category_name, 'JEWELRY')

    def _get_tracking_mode(self, product_type):
        """Determine appropriate tracking mode based on product type"""
        tracking_modes = {
            'RING': 'hand',
            'BRACELET': 'hand',
            'NECKLACE': 'face',
            'EARRING': 'face'
        }
        return tracking_modes.get(product_type, 'face')

    def _get_material_properties(self, product):
        """Get material-specific rendering properties"""
        material_properties = {
            "metallic": 1.0,
            "roughness": 0.2,
            "reflectivity": 0.8
        }
        
        if product.metaltype:
            if "gold" in product.metaltype.name.lower():
                material_properties.update({
                    "baseColor": "#FFD700",
                    "metallic": 0.95
                })
            elif "silver" in product.metaltype.name.lower():
                material_properties.update({
                    "baseColor": "#C0C0C0",
                    "metallic": 0.9
                })
                
        return material_properties

    async def _start_conversion(self, payload):
        """Start the 3D conversion process"""
        response = self.session.post(f"{self.base_url}/jewelry/convert3d", json=payload)
        response.raise_for_status()
        return response.json()['conversionId']

    async def _get_conversion_results(self, conversion_id):
        """Poll for conversion results"""
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            response = self.session.get(f"{self.base_url}/jewelry/convert3d/{conversion_id}")
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'completed':
                return data['modelData']
            elif data['status'] == 'failed':
                raise Exception(f"Conversion failed: {data.get('error')}")
            
            attempt += 1
            await asyncio.sleep(2)
        
        raise Exception("Conversion timeout")

    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.session:
                self.session.close()
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

    async def _prepare_processed_image(self, image_path):
        """Prepare the processed (background-removed) image for conversion"""
        try:
            full_path = os.path.join(settings.MEDIA_ROOT, image_path.lstrip('/media/'))
            img = Image.open(full_path)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Optimize image size
            target_size = 1024
            if img.width < target_size or img.height < target_size:
                ratio = target_size / min(img.width, img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)

            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', quality=95)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')

        except Exception as e:
            print(f"Error preparing processed image: {str(e)}")
            return None
