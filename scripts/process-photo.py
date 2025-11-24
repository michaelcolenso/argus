# scripts/process-photo.py
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image
import sys

def process_image(image_path, review_api_url=None, review_api_key=None):
    """Process a single image and return its metadata."""
    with Image.open(image_path) as img:
        width, height = img.size
        
        # Generate a hash of the image content for unique ID
        with open(image_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()[:12]
            
        # Get file stats
        stats = os.stat(image_path)
        
        analysis = {
            'id': file_hash,
            'filename': os.path.basename(image_path),
            'width': width,
            'height': height,
            'aspectRatio': width / height,
            'size': stats.st_size,
            'added': datetime.utcnow().isoformat(),
            'url': f'/photos/{os.path.basename(image_path)}',
            # Placeholder for AI analysis results - you can expand this
            'analysis': {
                'technical': {
                    'exposure': calculate_exposure(img),
                    'focus': 0,  # Placeholder for focus detection
                    'composition': 0  # Placeholder for composition analysis
                },
                'artistic': {
                    'impact': 0,
                    'creativity': 0,
                    'style': 0
                },
                'score': 0
            }
        }

        ai_review = None
        if review_api_url:
            ai_review = request_ai_review(image_path, review_api_url, review_api_key)

        if ai_review:
            analysis['analysis']['aiReview'] = ai_review

        return analysis

def calculate_exposure(img):
    """Basic exposure calculation based on image brightness."""
    # Convert to grayscale for brightness calculation
    gray = img.convert('L')
    # Calculate average brightness (0-255)
    histogram = gray.histogram()
    pixels = sum(histogram)
    brightness = sum(i * x for i, x in enumerate(histogram)) / pixels
    # Convert to 0-100 scale
    return (brightness / 255) * 100


def request_ai_review(image_path, api_url, api_key=None):
    """Send the image to an AI review service and return its structured feedback."""
    headers = {}
    if api_key:
        headers['Authorization'] = f"Bearer {api_key}"

    with open(image_path, 'rb') as file_handle:
        files = {'file': (os.path.basename(image_path), file_handle, 'application/octet-stream')}
        payload = {'filename': os.path.basename(image_path)}

        try:
            response = requests.post(api_url, headers=headers, files=files, data=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:  # noqa: BLE001 - capture any network/JSON failure
            print(f"AI review failed for {image_path.name}: {exc}", file=sys.stderr)
            return None

    # Expecting JSON with keys: summary, strengths, critique, actions
    summary = data.get('summary')
    strengths = data.get('strengths') or []
    critique = data.get('critique') or []
    actions = data.get('actions') or []

    if not summary:
        print(f"AI review missing summary for {image_path.name}", file=sys.stderr)
        return None

    return {
        'summary': summary,
        'strengths': strengths,
        'critique': critique,
        'actions': actions,
    }

def main():
    # Setup paths
    base_dir = Path(__file__).resolve().parent.parent
    photos_dir = base_dir / 'src' / 'photos'
    data_file = base_dir / 'src' / 'data' / 'photos.json'

    review_api_url = os.getenv('PHOTO_REVIEW_API_URL')
    review_api_key = os.getenv('PHOTO_REVIEW_API_KEY')
    
    # Load existing photo data
    if data_file.exists():
        with open(data_file) as f:
            photo_data = json.load(f)
    else:
        photo_data = {'photos': []}

    # Normalize existing photos into a dictionary keyed by id for quick lookup
    photos_store = {}
    for item in photo_data.get('photos', []):
        photo_id = item.get('id')
        if photo_id:
            photos_store[photo_id] = item

    current_photos = set()
    
    for image_file in photos_dir.glob('*'):
        if image_file.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif'}:
            file_hash = hashlib.sha256(image_file.read_bytes()).hexdigest()[:12]
            current_photos.add(file_hash)
            
            # Only process new or modified images
            if file_hash not in photos_store:
                print(f"Processing new image: {image_file.name}")
                photos_store[file_hash] = process_image(
                    image_file,
                    review_api_url=review_api_url,
                    review_api_key=review_api_key,
                )

    # Remove entries for deleted photos (only hashed IDs produced by this script)
    hashed_ids = {pid for pid in photos_store if len(pid) == 12}
    for old_hash in hashed_ids - current_photos:
        del photos_store[old_hash]

    # Save updated photo data
    with open(data_file, 'w') as f:
        json.dump({'photos': list(photos_store.values())}, f, indent=2)

if __name__ == '__main__':
    main()
