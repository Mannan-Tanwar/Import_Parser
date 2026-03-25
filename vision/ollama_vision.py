import pytesseract
import cv2
import numpy as np
from pathlib import Path
from PIL import Image

# Set Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Mannan.Tanwar\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# ─────────────────────────────────────────────
# Local OCR — Tesseract
# Extracts text from images completely locally
# No internet, no API, no model download needed
# Best accuracy for documents, forms, order slips
# ─────────────────────────────────────────────

# ── Windows users only ────────────────────────
# Uncomment and set your Tesseract install path:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def preprocess_image(image_path):
    """
    Preprocess the image before OCR to improve accuracy.

    Steps:
    1. Convert to grayscale       — removes colour noise
    2. Resize if too small        — tesseract works better on larger images
    3. Denoise                    — removes background noise
    4. Thresholding               — makes text crisp black on white
    5. Deskew                     — straightens slightly rotated scans

    Returns a processed image ready for OCR.
    """
    # Read image
    img = cv2.imread(str(image_path))

    if img is None:
        # Fallback to PIL if cv2 can't read it
        pil_img = Image.open(image_path).convert('RGB')
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # Step 1 — convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 2 — resize if image is too small
    # Tesseract works best at 300 DPI or higher
    height, width = gray.shape
    if width < 1000:
        scale = 2.0
        gray = cv2.resize(
            gray,
            (int(width * scale), int(height * scale)),
            interpolation=cv2.INTER_CUBIC
        )

    # Step 3 — denoise
    gray = cv2.fastNlMeansDenoising(gray, h=10)

    # Step 4 — adaptive thresholding
    # Makes text sharper — handles uneven lighting in photos
    processed = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    # Step 5 — deskew
    # Finds the angle of the text and rotates to straighten it
    coords = np.column_stack(np.where(processed > 0))
    if len(coords) > 0:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) > 0.5:  # only rotate if meaningfully skewed
            (h, w) = processed.shape
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            processed = cv2.warpAffine(
                processed, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )

    return processed


def extract_text_from_image(image_path):
    """
    Extract all text from an image using Tesseract OCR.
    Completely local — no internet required.

    Args:
        image_path: str or Path to the image file

    Returns:
        str — all text found in the image, preserving layout
    """
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    print(f"  Reading image: {image_path.name}")

    # Preprocess the image for better accuracy
    print(f"  Preprocessing image...")
    processed = preprocess_image(image_path)

    print(f"  Running OCR...")

    # Tesseract config:
    # --oem 3  → use best available OCR engine (LSTM neural net)
    # --psm 6  → assume a uniform block of text
    #            change to --psm 4 for single column
    #            change to --psm 3 for fully automatic layout detection
    config = '--oem 3 --psm 6'

    # Convert processed numpy array back to PIL for pytesseract
    pil_image = Image.fromarray(processed)

    # Run OCR
    extracted_text = pytesseract.image_to_string(
        pil_image,
        config=config,
        lang='eng'  # English — change if your docs are in another language
    )

    extracted_text = extracted_text.strip()

    if not extracted_text:
        raise ValueError(
            "No text could be extracted from this image.\n"
            "Possible reasons:\n"
            "  - Image is too blurry or low resolution\n"
            "  - Image is mostly blank\n"
            "  - Text is in an unusual font or handwritten"
        )

    print(f"  OCR complete.")
    return extracted_text


def extract_text_with_layout(image_path):
    """
    Extract text AND preserve the original layout/positioning.
    Returns text arranged to match the visual layout in the image.
    Better for forms and structured documents.

    Args:
        image_path: str or Path to the image file

    Returns:
        str — text preserving original column/row layout
    """
    image_path = Path(image_path)
    processed  = preprocess_image(image_path)
    pil_image  = Image.fromarray(processed)

    # Get detailed data including position of each word
    data = pytesseract.image_to_data(
        pil_image,
        config='--oem 3 --psm 6',
        lang='eng',
        output_type=pytesseract.Output.DICT
    )

    # Reconstruct layout by grouping words by their vertical position
    lines = {}
    n_boxes = len(data['text'])

    for i in range(n_boxes):
        word = data['text'][i].strip()
        conf = int(data['conf'][i])

        # Skip low confidence and empty results
        if conf < 30 or not word:
            continue

        top  = data['top'][i]
        left = data['left'][i]

        # Group words that are on the same line
        # (within 10 pixels of each other vertically)
        line_key = top // 10

        if line_key not in lines:
            lines[line_key] = []

        lines[line_key].append((left, word))

    # Sort lines top to bottom
    sorted_lines = sorted(lines.items(), key=lambda x: x[0])

    # Build output — sort words left to right within each line
    output_lines = []
    for _, words in sorted_lines:
        sorted_words = sorted(words, key=lambda x: x[0])
        line_text = '  '.join(w for _, w in sorted_words)
        output_lines.append(line_text)

    return '\n'.join(output_lines)


def check_tesseract_installed():
    """
    Check if Tesseract is installed and available.
    Returns (is_installed, message)
    """
    try:
        version = pytesseract.get_tesseract_version()
        return True, f"Tesseract {version} is installed and ready"
    except Exception:
        return False, (
            "Tesseract is not installed or not found.\n"
            "Install it:\n"
            "  Mac:     brew install tesseract\n"
            "  Linux:   sudo apt install tesseract-ocr\n"
            "  Windows: https://github.com/UB-Mannheim/tesseract/wiki\n\n"
            "Windows users also need to set the path in ollama_vision.py:\n"
            "  pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'"
        )



# ─────────────────────────────────────────────
# Ollama Vision Model — AI-powered image parsing
# Uses local vision model to understand and parse images
# ─────────────────────────────────────────────

import base64
import json
import requests

OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'qwen2.5vl:3b'


def image_to_base64(image_path):
    """Convert an image file to base64 string."""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def parse_image_with_ollama(image_path):
    """
    Use Ollama vision model to directly parse an image.
    The AI model looks at the image and extracts structured information.
    
    Args:
        image_path: str or Path to the image file
        
    Returns:
        str — structured text extracted by the AI model
    """
    image_path = Path(image_path)
    
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    print(f"  Reading image: {image_path.name}")
    b64_image = image_to_base64(image_path)
    
    print(f"  Sending to Ollama vision model ({OLLAMA_MODEL})...")
    print(f"  This may take 1-3 minutes...")
    print(f"  Processing", end="", flush=True)
    
    # Prompt for the vision model
    prompt = """Analyze this image and extract all information in a well-structured format.

Please organize the output using these sections:

═══════════════════════════════════════════════
DOCUMENT INFORMATION
═══════════════════════════════════════════════
Document Type: [type of document - form, invoice, order, etc.]
Title/Header: [main title or header text]
Date: [any date found]
Reference/Order Number: [any reference numbers]

═══════════════════════════════════════════════
CUSTOMER/RECIPIENT INFORMATION
═══════════════════════════════════════════════
Name: [full name]
Address Line 1: [street address]
Address Line 2: [city, state, zip]
Phone: [phone number if present]
Email: [email if present]

═══════════════════════════════════════════════
PRODUCT/SERVICE DETAILS
═══════════════════════════════════════════════
Item/Service: [what is being ordered/purchased]
Quantity: [quantity if specified]
Duration/Period: [subscription period, service duration, etc.]

═══════════════════════════════════════════════
PRICING INFORMATION
═══════════════════════════════════════════════
Original Price: [regular price]
Discount/Savings: [discount amount or percentage]
Final Price: [discounted/final price]
Currency: [USD, EUR, etc.]

═══════════════════════════════════════════════
PAYMENT INFORMATION
═══════════════════════════════════════════════
Payment Method: [check, credit card, etc.]
Payment Status: [enclosed, bill later, etc.]
Payment Details: [any additional payment info]

═══════════════════════════════════════════════
ADDITIONAL INFORMATION
═══════════════════════════════════════════════
[Any other relevant information, notes, terms, conditions, etc.]

═══════════════════════════════════════════════

If any section is not applicable or information is not found, write "Not specified" or "N/A".
Be precise and extract exact values from the image."""
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                'model': OLLAMA_MODEL,
                'prompt': prompt,
                'images': [b64_image],
                'stream': True,
                'options': {
                    'temperature': 0,
                    'num_predict': 2048,
                },
            },
            timeout=300,
            stream=True
        )
        response.raise_for_status()
        
        # Collect streamed response
        extracted_text = ""
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                if 'response' in chunk:
                    extracted_text += chunk['response']
                    print(".", end="", flush=True)
                if chunk.get('done', False):
                    break
        print()  # New line after dots
        
        extracted_text = extracted_text.strip()
        
        if not extracted_text:
            raise ValueError("Model returned no text")
        
        print(f"  ✓ AI parsing complete")
        return extracted_text
        
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Cannot connect to Ollama at localhost:11434.\n"
            "Make sure Ollama is running:\n"
            "  ollama serve\n"
            "And the vision model is installed:\n"
            f"  ollama pull {OLLAMA_MODEL}"
        )
    except requests.exceptions.ReadTimeout:
        raise TimeoutError(
            f"Ollama took too long to respond (>300 seconds).\n"
            f"The image might be too large or complex."
        )


def check_ollama_running():
    """
    Check if Ollama is running and the vision model is available.
    Returns (is_running, is_model_available, message)
    """
    try:
        response = requests.get(
            'http://localhost:11434/api/tags',
            timeout=5
        )
        models = response.json().get('models', [])
        model_names = [m['name'] for m in models]
        
        model_available = any(
            OLLAMA_MODEL in name for name in model_names
        )
        
        if model_available:
            return True, True, f"Ollama running, {OLLAMA_MODEL} available"
        else:
            return True, False, (
                f"Ollama running but {OLLAMA_MODEL} not found.\n"
                f"Available models: {model_names}\n"
                f"Run: ollama pull {OLLAMA_MODEL}"
            )
    
    except requests.exceptions.ConnectionError:
        return False, False, (
            "Ollama not running.\n"
            "Start it with: ollama serve"
        )
