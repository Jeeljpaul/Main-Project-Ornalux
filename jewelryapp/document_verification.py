import os
import tensorflow as tf
from PIL import Image
import numpy as np
import re
from datetime import datetime
from pdf2image import convert_from_path
import pdfplumber
import PyPDF2

class BusinessDocumentVerifier:
    def __init__(self):
        # Create a simple CNN model first
        self.model = tf.keras.Sequential([
            tf.keras.layers.Conv2D(32, 3, activation='relu', input_shape=(224, 224, 3)),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(64, 3, activation='relu'),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(64, 3, activation='relu'),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        # Keep reference as feature_model
        self.feature_model = self.model
        
        # Create a CNN model for document authenticity
        self.authenticity_model = tf.keras.Sequential([
            tf.keras.layers.Conv2D(64, 3, activation='relu', input_shape=(224, 224, 3)),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(128, 3, activation='relu'),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(128, 3, activation='relu'),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.4),
            tf.keras.layers.Dense(2, activation='softmax')  # [real_prob, ai_generated_prob]
        ])
        
        # Document patterns for different types with required and optional fields
        self.document_patterns = {
            'incorporation': {
                'required': {
                    'name': r'(certificate|cert).*incorporation|incorporation.*certificate|company.*registration',
                },
                'optional': {
                    'cin': r'[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}',  # Company Identification Number
                    'date': r'dated?\s*[:|-]?\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})',
                }
            },
            'gst': {
                'required': {
                    'name': r'gst|goods\s*and\s*services\s*tax|tax\s*registration',
                },
                'optional': {
                    'number': r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}',  # GST Number
                    'pan': r'[A-Z]{5}\d{4}[A-Z]{1}',  # PAN Number
                }
            },
            'trade_license': {
                'required': {
                    'name': r'trade\s*license|business\s*license|commercial\s*license',
                },
                'optional': {
                    'number': r'[A-Z0-9-/]+',
                    'validity': r'valid(?:ity)?\s*(?:till|until|up\s*to|expires?)\s*[-:]?\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})',
                }
            },
            'partnership_deed': {
                'required': {
                    'name': r'partnership\s*deed|partnership\s*agreement|deed\s*of\s*partnership',
                },
                'optional': {
                    'date': r'dated?\s*[:|-]?\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})',
                    'partners': r'partners?\s*[:|-]?\s*([^.]+)',
                }
            },
            'proprietorship': {
                'required': {
                    'name': r'proprietorship|sole\s*proprietor|proprietor\s*declaration',
                },
                'optional': {
                    'proprietor': r'proprietor\s*[:|-]?\s*([^.]+)',
                    'business_name': r'(?:business|firm)\s*name\s*[:|-]?\s*([^.]+)',
                }
            }
        }

    def preprocess_image(self, image_path):
        """Preprocess image for the model"""
        try:
            # Load and resize image
            image = Image.open(image_path)
            image = image.resize((224, 224))
            image = image.convert('RGB')
            
            # Convert to array and normalize
            image_array = np.array(image) / 255.0
            image_array = np.expand_dims(image_array, 0)
            return image_array
        except Exception as e:
            raise Exception(f"Error preprocessing image: {str(e)}")

    def extract_text_from_image(self, image_path):
        """Extract text from image using OCR"""
        try:
            import pytesseract
            
            # Configure Tesseract path for Windows
            if os.name == 'nt':  # Windows
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            
            # Open and preprocess image for better OCR
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Increase size for better OCR
            width, height = image.size
            if width < 1000:
                ratio = 1000.0 / width
                image = image.resize((1000, int(height * ratio)), Image.Resampling.LANCZOS)
            
            # Convert to grayscale for better OCR performance
            image = image.convert('L')  # Convert to grayscale
            
            # Apply thresholding to binarize the image
            image = image.point(lambda x: 0 if x < 128 else 255, '1')  # Simple thresholding
            
            # Extract text with improved configuration
            text = pytesseract.image_to_string(
                image,
                config='--oem 3 --psm 6 -c preserve_interword_spaces=1'
            )
            
            # Clean and normalize text
            text = text.lower().replace('\n', ' ')
            text = re.sub(r'\s+', ' ', text)
            
            print(f"Extracted text: {text[:200]}...")  # Debug print
            return text
            
        except ImportError:
            print("Tesseract not installed. Please install Tesseract OCR.")
            return ""
        except Exception as e:
            print(f"OCR Error: {str(e)}")  # Improved error message
            return ""

    def analyze_image_quality(self, image_array):
        """Analyze image quality metrics"""
        try:
            # Calculate basic image statisticssac
            mean_val = np.mean(image_array)
            std_val = np.std(image_array)
            
            # Simple quality metrics
            brightness_score = 1.0 - abs(0.5 - mean_val)  # Optimal brightness around 0.5
            contrast_score = min(std_val * 2, 1.0)  # Higher contrast is better, up to a point
            
            return (brightness_score + contrast_score) / 2
        except:
            return 0.5

    def detect_ai_generated(self, image_array):
        """Detect if the document is AI-generated using CNN"""
        try:
            # Get predictions from authenticity model
            predictions = self.authenticity_model.predict(image_array)
            real_prob = predictions[0][0]
            ai_generated_prob = predictions[0][1]
            
            # Analyze specific features that might indicate AI generation
            features = {
                'uniform_patterns': self._check_uniform_patterns(image_array),
                'artifact_detection': self._check_artifacts(image_array),
                'texture_analysis': self._analyze_texture(image_array)
            }
            
            return {
                'is_ai_generated': ai_generated_prob > 0.6,
                'confidence': max(real_prob, ai_generated_prob),
                'ai_generation_probability': ai_generated_prob,
                'feature_analysis': features,
                'suspicious_elements': self._identify_suspicious_elements(features)
            }
        except Exception as e:
            print(f"AI detection error: {str(e)}")
            return {
                'is_ai_generated': False,
                'confidence': 0.5,
                'ai_generation_probability': 0.0,
                'feature_analysis': {},
                'suspicious_elements': []
            }

    def _check_uniform_patterns(self, image_array):
        """Check for suspiciously uniform patterns"""
        std_dev = np.std(image_array)
        return std_dev < 0.1  # Returns True if patterns are too uniform

    def _check_artifacts(self, image_array):
        """Check for common AI generation artifacts"""
        # Simple edge detection to find unnatural artifacts
        edges = np.diff(image_array)
        return np.mean(np.abs(edges)) > 0.5

    def _analyze_texture(self, image_array):
        """Analyze texture patterns for AI indicators"""
        gray = np.mean(image_array, axis=-1)
        texture_score = np.var(gray)
        return texture_score < 0.2  # Returns True if texture seems artificial

    def _identify_suspicious_elements(self, features):
        """Identify which elements seem suspicious"""
        suspicious = []
        if features['uniform_patterns']:
            suspicious.append('Unusually uniform patterns detected')
        if features['artifact_detection']:
            suspicious.append('Artificial artifacts present')
        if features['texture_analysis']:
            suspicious.append('Unnatural texture patterns')
        return suspicious

    def check_document_forgery(self, image_array):
        """Enhanced forgery detection including AI generation check"""
        try:
            # Get basic image quality score
            quality_score = float(self.analyze_image_quality(image_array))
            
            # Check for AI generation
            ai_detection = self.detect_ai_generated(image_array)
            
            # Combine both analyses
            forgery_probability = float(max(
                1.0 - quality_score,
                ai_detection['ai_generation_probability']
            ))
            
            return {
                'is_forged': str(forgery_probability > 0.7),  # Convert to string
                'is_ai_generated': str(ai_detection['is_ai_generated']),  # Convert to string
                'confidence': float(1.0 - forgery_probability),  # Ensure float
                'forgery_probability': float(forgery_probability),  # Ensure float
                'ai_generation_details': {
                    'is_ai_generated': str(ai_detection['is_ai_generated']),
                    'confidence': float(ai_detection['confidence']),
                    'ai_generation_probability': float(ai_detection['ai_generation_probability']),
                    'feature_analysis': {
                        'uniform_patterns': str(ai_detection['feature_analysis'].get('uniform_patterns', False)),
                        'artifact_detection': str(ai_detection['feature_analysis'].get('artifact_detection', False)),
                        'texture_analysis': str(ai_detection['feature_analysis'].get('texture_analysis', False))
                    },
                    'suspicious_elements': list(ai_detection['suspicious_elements'])
                },
                'quality_score': float(quality_score),
                'suspicious_elements': list(ai_detection['suspicious_elements'])
            }
        except Exception as e:
            print(f"Forgery check error: {str(e)}")
            return {
                'is_forged': 'false',
                'is_ai_generated': 'false',
                'confidence': 0.5,
                'forgery_probability': 0.5,
                'ai_generation_details': {
                    'is_ai_generated': 'false',
                    'confidence': 0.5,
                    'ai_generation_probability': 0.0,
                    'feature_analysis': {},
                    'suspicious_elements': []
                },
                'quality_score': 0.5,
                'suspicious_elements': []
            }

    def is_image_file(self, file_path):
        """Check if the file is an image or PDF based on its extension"""
        valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.pdf')
        return file_path.lower().endswith(valid_extensions)

    def convert_pdf_to_image(self, pdf_path):
        """Convert first page of PDF to image"""
        try:
            # Verify the file exists and is a PDF
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            if not pdf_path.lower().endswith('.pdf'):
                raise ValueError(f"File is not a PDF: {pdf_path}")

            # For Windows: Try to automatically find Poppler path
            if os.name == 'nt':  # Windows
                poppler_paths = [
                    r'C:\Program Files\poppler-23.11.0\Library\bin',  # Default install path
                    r'C:\Program Files\poppler-0.68.0\bin',           # Alternate path
                    r'C:\poppler-23.11.0\Library\bin',               # Custom path
                    r'C:\poppler\bin',                               # Custom path
                ]
                
                # Try to find poppler in PATH
                for path in poppler_paths:
                    if os.path.exists(path):
                        os.environ['PATH'] = path + os.pathsep + os.environ['PATH']
                        break

            # Try to convert PDF to image with detailed error handling
            try:
                images = convert_from_path(
                    pdf_path,
                    first_page=1,
                    last_page=1,
                    dpi=200,
                    fmt='PNG',
                    poppler_path=None if os.name != 'nt' else os.environ.get('POPPLER_PATH')
                )
                if not images:
                    raise ValueError("No images extracted from PDF")
                return images[0]
            except Exception as pdf_error:
                error_msg = str(pdf_error)
                if "poppler" in error_msg.lower():
                    raise Exception(
                        "Poppler is not properly installed. Please install Poppler and set the path:\n"
                        "1. Download Poppler from https://github.com/oschwartz10612/poppler-windows/releases\n"
                        "2. Extract to C:\\poppler-23.11.0\n"
                        "3. Add C:\\poppler-23.11.0\\Library\\bin to your system PATH\n"
                        "4. Restart your application"
                    )
                raise Exception(f"Failed to convert PDF: {error_msg}")

        except Exception as e:
            print(f"PDF processing error: {str(e)}")
            return None

    def extract_text_from_pdf(self, pdf_path):
        """Extract text directly from PDF"""
        try:
            text = ""
            # Try with pdfplumber first (better for formatted text)
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            
            # If no text was extracted, try PyPDF2 as fallback
            if not text.strip():
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text() or ""

            # Clean and normalize text
            text = text.lower().replace('\n', ' ')
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

        except Exception as e:
            print(f"PDF text extraction error: {str(e)}")
            return ""

    def verify_document(self, document_path):
        """Main verification method"""
        try:
            # Basic file validation
            if not os.path.exists(document_path):
                return {
                    'success': False,
                    'message': f'Document file not found: {document_path}'
                }
            
            # Check if the file is an image or PDF
            if not self.is_image_file(document_path):
                return {
                    'success': False,
                    'message': f'Uploaded file is not a valid image or PDF: {document_path}'
                }

            # Extract text for document type verification
            text = ""
            if document_path.lower().endswith('.pdf'):
                text = self.extract_text_from_pdf(document_path)
            else:
                text = self.extract_text_from_image(document_path)

            # Verify if it's a business document
            document_type = None
            for doc_type, patterns in self.document_patterns.items():
                required_patterns = patterns['required']
                # Check if all required patterns are found
                if all(re.search(pattern, text, re.IGNORECASE) for pattern in required_patterns.values()):
                    document_type = doc_type
                    break

            if not document_type:
                return {
                    'success': False,
                    'message': 'The uploaded document is not a recognized business document'
                }

            # Handle different file types
            if document_path.lower().endswith('.pdf'):
                # Extract text directly from PDF
                text = self.extract_text_from_pdf(document_path)
                if not text:
                    return {
                        'success': False,
                        'message': 'Could not extract text from PDF'
                    }
                
                # Process the extracted text
                # You can add your text verification logic here
                verification_confidence = 75.0  # Example confidence score
                
                return {
                    'success': True,
                    'is_valid': True,
                    'details': {
                        'verification_confidence': f"{verification_confidence:.1f}%",
                        'text_extracted': True,
                        'document_type': 'PDF'
                    }
                }
            else:
                # Handle image files with existing image processing logic
                try:
                    image = Image.open(document_path)
                    image = image.resize((224, 224))
                    image = image.convert('RGB')
                    image_array = np.array(image) / 255.0
                except Exception as img_error:
                    return {
                        'success': False,
                        'message': f'Failed to process image: {str(img_error)}'
                    }
                
                # Continue with existing image verification logic
                forgery_check = self.check_document_forgery(image_array)
                
                # Calculate verification confidence
                forgery_prob = float(forgery_check['forgery_probability'])
                quality_score = float(forgery_check['quality_score'])
                
                if np.isnan(forgery_prob) or np.isnan(quality_score):
                    verification_confidence = 50.0
                else:
                    verification_confidence = (
                        (1 - forgery_prob) * 0.6 +
                        quality_score * 0.4
                    ) * 100
                
                verification_confidence = max(0, min(100, verification_confidence))

                return {
                    'success': True,
                    'forgery_analysis': forgery_check,
                    'is_valid': not forgery_check['is_forged'],
                    'details': {
                        'verification_confidence': f"{verification_confidence:.1f}%",
                        'forgery_confidence': f"{max(0, min(100, forgery_check['confidence']*100)):.1f}%",
                        'quality_score': f"{max(0, min(100, quality_score*100)):.1f}%"
                    }
                }

        except Exception as e:
            return {
                'success': False,
                'message': f"Error verifying document: {str(e)}"
            } 