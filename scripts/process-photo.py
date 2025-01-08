# scripts/process-photo.py
import os
import json
import hashlib
from datetime import datetime
from PIL import Image
import sys
from pathlib import Path

def process_image(image_path):
    """Process a single image and return its metadata."""
    with Image.open(image_path) as img:
        width, height = img.size
        
        # Generate a hash of the image content for unique ID
        with open(image_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()[:12]
            
        # Get file stats
        stats = os.stat(image_path)
        
        return {
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

def main():
    # Setup paths
    base_dir = Path(__file__).resolve().parent.parent
    photos_dir = base_dir / 'src' / 'photos'
    data_file = base_dir / 'src' / 'data' / 'photos.json'
    
    # Load existing photo data
    if data_file.exists():
        with open(data_file) as f:
            photo_data = json.load(f)
    else:
        photo_data = {'photos': {}}
    
    # Process all images in the photos directory
    existing_photos = set(photo_data['photos'].keys())
    current_photos = set()
    
    for image_file in photos_dir.glob('*'):
        if image_file.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif'}:
            file_hash = hashlib.sha256(image_file.read_bytes()).hexdigest()[:12]
            current_photos.add(file_hash)
            
            # Only process new or modified images
            if file_hash not in photo_data['photos']:
                print(f"Processing new image: {image_file.name}")
                photo_data['photos'][file_hash] = process_image(image_file)
    
    # Remove entries for deleted photos
    for old_hash in existing_photos - current_photos:
        del photo_data['photos'][old_hash]
    
    # Save updated photo data
    with open(data_file, 'w') as f:
        json.dump(photo_data, f, indent=2)

if __name__ == '__main__':
    main()