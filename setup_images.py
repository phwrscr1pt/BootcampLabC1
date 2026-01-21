#!/usr/bin/env python3
"""
Setup script to download high-quality flower images from Unsplash.
Run this script before starting the Flask application.
"""

import os
import requests
import time

# Unsplash image URLs (high-quality flower images)
FLOWER_IMAGES = [
    "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=800&q=80",  # Pink roses
    "https://images.unsplash.com/photo-1518882605630-8eb favor-f172a30b5b87?w=800&q=80",  # White flowers
    "https://images.unsplash.com/photo-1455659817273-f96807779a8a?w=800&q=80",  # Tulips
    "https://images.unsplash.com/photo-1487530811176-3780de880c2d?w=800&q=80",  # Red roses
    "https://images.unsplash.com/photo-1508610048659-a06b669e3321?w=800&q=80",  # Sunflowers
    "https://images.unsplash.com/photo-1526047932273-341f2a7631f9?w=800&q=80",  # Pink peonies
    "https://images.unsplash.com/photo-1444021465936-c6ca81d39b84?w=800&q=80",  # Lavender
    "https://images.unsplash.com/photo-1518882605630-8eb1f1f1c7eb?w=800&q=80",  # White roses
    "https://images.unsplash.com/photo-1502977249166-824b3a8a4d6d?w=800&q=80",  # Mixed bouquet
    "https://images.unsplash.com/photo-1469259943454-aa100abba749?w=800&q=80",  # Orchids
]

# Backup URLs in case primary ones fail
BACKUP_IMAGES = [
    "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=800&q=80",
    "https://images.unsplash.com/photo-1518882605630-8eb1f1f1c7eb?w=800&q=80",
    "https://images.unsplash.com/photo-1455659817273-f96807779a8a?w=800&q=80",
    "https://images.unsplash.com/photo-1487530811176-3780de880c2d?w=800&q=80",
    "https://images.unsplash.com/photo-1508610048659-a06b669e3321?w=800&q=80",
    "https://images.unsplash.com/photo-1526047932273-341f2a7631f9?w=800&q=80",
    "https://images.unsplash.com/photo-1444021465936-c6ca81d39b84?w=800&q=80",
    "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=800&q=80",
    "https://images.unsplash.com/photo-1502977249166-824b3a8a4d6d?w=800&q=80",
    "https://images.unsplash.com/photo-1469259943454-aa100abba749?w=800&q=80",
]

def download_images():
    """Download flower images to static/images/ directory."""

    # Create directory if it doesn't exist
    images_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
    os.makedirs(images_dir, exist_ok=True)

    print("=" * 50)
    print("  LOCth Shop - Image Setup Script")
    print("=" * 50)
    print(f"\nDownloading {len(FLOWER_IMAGES)} flower images...\n")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    success_count = 0

    for i, url in enumerate(FLOWER_IMAGES, 1):
        filename = f"flower_{i}.jpg"
        filepath = os.path.join(images_dir, filename)

        # Skip if file already exists
        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            print(f"[{i}/10] {filename} already exists, skipping...")
            success_count += 1
            continue

        try:
            print(f"[{i}/10] Downloading {filename}...", end=" ")
            response = requests.get(url, headers=headers, timeout=30, stream=True)

            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print("Done!")
                success_count += 1
            else:
                # Try backup URL
                print(f"Failed (HTTP {response.status_code}), trying backup...")
                backup_url = BACKUP_IMAGES[i - 1]
                response = requests.get(backup_url, headers=headers, timeout=30, stream=True)
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print("Done (backup)!")
                    success_count += 1
                else:
                    print(f"Backup also failed!")

        except requests.exceptions.RequestException as e:
            print(f"Error: {str(e)[:50]}")

        # Small delay to be respectful to the server
        time.sleep(0.5)

    print("\n" + "=" * 50)
    print(f"  Download complete: {success_count}/10 images")
    print("=" * 50)

    if success_count < 10:
        print("\nNote: Some images failed to download.")
        print("You can manually add flower images named flower_1.jpg through flower_10.jpg")
        print(f"to the directory: {images_dir}")

    return success_count

if __name__ == "__main__":
    download_images()
