import os
import glob
from pathlib import Path
from datetime import datetime

def select_images(layer_id=1, limit=100):
    """画像一覧を取得する"""
    parent_dir = Path(__file__).parent
    image_dir = parent_dir / 'plant_images' / f'layer_{layer_id}'
    
    if not image_dir.exists():
        return []

    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        image_files.extend(glob.glob(str(image_dir / ext)))
    
    images = []
    for file_path in image_files:
        filename = os.path.basename(file_path)
        try:
            date_str = filename.split('.')[0]
            timestamp = datetime.strptime(date_str, '%Y%m%d_%H%M%S').isoformat()
        except ValueError:
            mtime = os.path.getmtime(file_path)
            timestamp = datetime.fromtimestamp(mtime).isoformat()
        
        relative_path = f'plant_images/layer_{layer_id}/{filename}'
        images.append({'image_path': relative_path, 'timestamp': timestamp, 'filename': filename})
    
    images.sort(key=lambda x: x['timestamp'], reverse=True)
    return images[:limit]