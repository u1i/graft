#!/usr/bin/env python3
"""
Graft - Image Generation CLI Tool
A sister project to Glean for generating images using OpenRouter API.
"""

import argparse
import configparser
import json
import os
import sys
import time
import tempfile
import requests
import urllib3
import base64
import mimetypes
from pathlib import Path
from datetime import datetime
import re

# Suppress SSL warnings when verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GraftConfig:
    """Handle configuration loading and validation."""
    
    def __init__(self):
        self.config_path = Path.home() / '.graft_cfg'
        self.api_key = None
        self.model = 'google/gemini-2.5-flash-image-preview'  # Default image model
        self.temperature = 0.7  # Default temperature for image generation
        self.system_prompt = None  # Optional system prompt
        self.http_proxy = None  # Optional HTTP proxy
        
    def load_config(self):
        """Load configuration from ~/.graft_cfg file."""
        if not self.config_path.exists():
            print(f"Error: Configuration file not found at {self.config_path}")
            print("Please create ~/.graft_cfg with your OpenRouter API key.")
            print("See README.md for configuration format.")
            sys.exit(1)
            
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path)
            
            # Required settings
            self.api_key = config.get('openrouter', 'api_key')
            
            # Optional settings with defaults
            if config.has_option('openrouter', 'model'):
                self.model = config.get('openrouter', 'model')
            
            if config.has_option('openrouter', 'temperature'):
                self.temperature = config.getfloat('openrouter', 'temperature')
                
            if config.has_option('openrouter', 'system_prompt'):
                self.system_prompt = config.get('openrouter', 'system_prompt')
                
            if config.has_option('openrouter', 'http_proxy'):
                self.http_proxy = config.get('openrouter', 'http_proxy')
                
        except Exception as e:
            print(f"Error loading configuration: {e}")
            sys.exit(1)


class GraftAPI:
    """Handle OpenRouter API interactions."""
    
    def __init__(self, config):
        self.config = config
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.models_url = "https://openrouter.ai/api/v1/models"
        
    def generate_image(self, prompt_text, input_image_path=None, input_image_data=None):
        """Generate an image using the configured model."""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/u1i/graft",
            "X-Title": "Graft CLI Tool"
        }
        
        messages = []
        if self.config.system_prompt:
            messages.append({
                "role": "system",
                "content": self.config.system_prompt
            })
        
        # Build user message content
        user_content = []
        
        # Add text prompt
        user_content.append({
            "type": "text",
            "text": prompt_text
        })
        
        # Add image if provided (from file or data)
        image_data = None
        mime_type = None
        
        if input_image_path:
            if not os.path.exists(input_image_path):
                raise FileNotFoundError(f"Input image not found: {input_image_path}")
            
            # Read and encode image from file
            with open(input_image_path, 'rb') as f:
                image_data = f.read()
            
            # Get MIME type from file extension
            mime_type, _ = mimetypes.guess_type(input_image_path)
            if not mime_type or not mime_type.startswith('image/'):
                mime_type = 'image/png'  # Default fallback
                
        elif input_image_data:
            # Use image data directly
            image_data = input_image_data
            
            # Detect MIME type from image data
            if image_data.startswith(b'\xFF\xD8\xFF'):
                mime_type = 'image/jpeg'
            elif image_data.startswith(b'\x89PNG\r\n\x1a\n'):
                mime_type = 'image/png'
            elif image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a'):
                mime_type = 'image/gif'
            elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:12]:
                mime_type = 'image/webp'
            elif image_data.startswith(b'BM'):
                mime_type = 'image/bmp'
            else:
                mime_type = 'image/png'  # Default fallback
        
        if image_data:
            # Encode as base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}"
                }
            })
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        data = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature
        }
        
        # Setup proxy if configured
        proxies = {}
        if self.config.http_proxy:
            proxies = {
                'http': self.config.http_proxy,
                'https': self.config.http_proxy
            }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, proxies=proxies, verify=False)
            response.raise_for_status()
            
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0]['message']
                
                # Check for images first
                if 'images' in message and message['images']:
                    images = message['images']
                    
                    for i, image in enumerate(images):
                        if 'image_url' in image and 'url' in image['image_url']:
                            image_url = image['image_url']['url']
                            
                            # Check if it's a base64 data URL
                            if image_url.startswith('data:image/'):
                                # Extract base64 data
                                header, data = image_url.split(',', 1)
                                image_data = base64.b64decode(data)
                                
                                # Use custom filename or generate one
                                if hasattr(self, 'custom_filename') and self.custom_filename:
                                    if self.custom_filename == '-':
                                        if i == 0:  # Only output first image to stdout
                                            sys.stdout.buffer.write(image_data)
                                            return f"Image output to stdout"
                                        else:
                                            continue  # Skip additional images when outputting to stdout
                                    else:
                                        # Handle multiple images with custom filename
                                        if i == 0:
                                            filename = self.custom_filename
                                        else:
                                            # Add suffix for additional images: image.png -> image_2.png, image_3.png
                                            base, ext = os.path.splitext(self.custom_filename)
                                            filename = f"{base}_{i+1}{ext}"
                                else:
                                    filename = generate_filename(prompt_text) if i == 0 else generate_filename(prompt_text).replace('.png', f'_{i+1}.png')
                                
                                if hasattr(self, 'custom_filename') and self.custom_filename == '-':
                                    # Already handled above
                                    pass
                                else:
                                    try:
                                        with open(filename, 'wb') as f:
                                            f.write(image_data)
                                        print(f"✅ Image {i+1} saved successfully: {filename}", file=sys.stderr)
                                    except Exception as e:
                                        print(f"❌ Failed to save image {i+1}: {e}", file=sys.stderr)
                            else:
                                # Regular URL - download it
                                if hasattr(self, 'custom_filename') and self.custom_filename:
                                    if self.custom_filename == '-':
                                        if i == 0:  # Only output first image to stdout
                                            try:
                                                response = requests.get(image_url, stream=True, verify=False)
                                                response.raise_for_status()
                                                sys.stdout.buffer.write(response.content)
                                                return f"Image output to stdout"
                                            except Exception as e:
                                                print(f"❌ Failed to download image: {e}", file=sys.stderr)
                                                return None
                                        else:
                                            continue  # Skip additional images when outputting to stdout
                                    else:
                                        # Handle multiple images with custom filename
                                        if i == 0:
                                            filename = self.custom_filename
                                        else:
                                            # Add suffix for additional images: image.png -> image_2.png, image_3.png
                                            base, ext = os.path.splitext(self.custom_filename)
                                            filename = f"{base}_{i+1}{ext}"
                                else:
                                    filename = generate_filename(prompt_text) if i == 0 else generate_filename(prompt_text).replace('.png', f'_{i+1}.png')
                                
                                if hasattr(self, 'custom_filename') and self.custom_filename == '-':
                                    # Already handled above
                                    pass
                                else:
                                    if download_image(image_url, filename):
                                        print(f"✅ Image {i+1} saved successfully: {filename}", file=sys.stderr)
                                    else:
                                        print(f"❌ Failed to download image {i+1} from: {image_url}", file=sys.stderr)
                    
                    return f"Generated {len(images)} image(s)"
                
                content = message.get('content', '')
                
                # Try to extract image URL from the response
                if content.startswith('http'):
                    image_url = content.strip()
                else:
                    image_url = extract_image_url(content)
                
                if image_url:
                    # Generate filename and download image
                    filename = generate_filename(prompt_text)
                    print(f"Downloading image to: {filename}")
                    
                    if download_image(image_url, filename):
                        print(f"✅ Image saved successfully: {filename}")
                        return f"Image saved as: {filename}\nImage URL: {image_url}"
                    else:
                        print(f"❌ Failed to download image from: {image_url}")
                        return f"Image URL found but download failed: {image_url}"
                else:
                    print("No image URL found in response. Generated content:")
                    print(content)
                    return content
            else:
                print("Error: Unexpected API response format.")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing API response: {e}")
            return None


def read_stdin():
    """Read text from stdin."""
    try:
        return sys.stdin.read()
    except Exception as e:
        print(f"Error reading from stdin: {e}")
        sys.exit(1)


def read_stdin_binary():
    """Read binary data from stdin."""
    try:
        return sys.stdin.buffer.read()
    except Exception as e:
        print(f"Error reading binary data from stdin: {e}")
        sys.exit(1)


def is_binary_data(data):
    """Check if data appears to be binary (image) data."""
    if isinstance(data, bytes):
        # Check for common image file signatures
        image_signatures = [
            b'\xFF\xD8\xFF',  # JPEG
            b'\x89PNG\r\n\x1a\n',  # PNG
            b'GIF87a',  # GIF87a
            b'GIF89a',  # GIF89a
            b'RIFF',  # WebP (starts with RIFF)
            b'BM',  # BMP
        ]
        
        for sig in image_signatures:
            if data.startswith(sig):
                return True
        
        # Also check if data contains mostly non-printable characters
        try:
            data.decode('utf-8')
            return False  # If it decodes as UTF-8, probably text
        except UnicodeDecodeError:
            return True  # If it can't decode, probably binary
    
    return False


def download_image(url, filename):
    """Download image from URL and save to disk."""
    try:
        response = requests.get(url, stream=True, verify=False)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"Error downloading image: {e}")
        return False


def extract_image_url(content):
    """Extract image URL from API response content."""
    # Look for URLs in the content
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
    
    # Filter for image URLs
    image_urls = []
    for url in urls:
        if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
            image_urls.append(url)
    
    return image_urls[0] if image_urls else None


def generate_filename(prompt_text):
    """Generate a safe filename from the prompt text."""
    # Clean the prompt for filename
    safe_prompt = re.sub(r'[^\w\s-]', '', prompt_text)
    safe_prompt = re.sub(r'[-\s]+', '_', safe_prompt)
    safe_prompt = safe_prompt[:50]  # Limit length
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"graft_{timestamp}_{safe_prompt}.png"


def get_cache_file_path():
    """Get the path for the models cache file."""
    return os.path.join(tempfile.gettempdir(), 'graft_models_cache.json')


def is_cache_valid(cache_file_path, max_age_hours=6):
    """Check if the cache file exists and is not older than max_age_hours."""
    if not os.path.exists(cache_file_path):
        return False
    
    file_age = time.time() - os.path.getmtime(cache_file_path)
    max_age_seconds = max_age_hours * 3600
    return file_age < max_age_seconds


def fetch_models_data():
    """Fetch models data from OpenRouter API with caching."""
    cache_file = get_cache_file_path()
    
    # Check if cache is valid
    if is_cache_valid(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass  # If cache read fails, fetch fresh data
    
    # Fetch fresh data
    try:
        response = requests.get('https://openrouter.ai/api/v1/models', verify=False)
        response.raise_for_status()
        data = response.json()
        
        # Cache the data
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass  # If caching fails, continue with fresh data
        
        return data
    except Exception as e:
        print(f"Error fetching models data: {e}")
        return {'data': []}


def list_models(detailed=False):
    """List available image generation models."""
    try:
        models_data = fetch_models_data()
        
        if 'data' in models_data:
            models = models_data['data']
        else:
            models = models_data  # Fallback if response format is different
        
        # Filter models that have 'image' in their output modalities
        image_models = []
        for model in models:
            architecture = model.get('architecture', {})
            output_modalities = architecture.get('output_modalities', [])
            if 'image' in output_modalities:
                image_models.append(model)
        
        if detailed:
            print(f"Available OpenRouter Image Generation Models ({len(image_models)} total):")
            print("=" * 70)
            
            for model in image_models:
                model_id = model.get('id', 'Unknown')
                name = model.get('name', 'Unknown')
                context_length = model.get('context_length', 'Unknown')
                pricing = model.get('pricing', {})
                prompt_price = pricing.get('prompt', 'Unknown')
                completion_price = pricing.get('completion', 'Unknown')
                description = model.get('description', 'No description available')
                
                print(f"ID: {model_id}")
                print(f"Name: {name}")
                print(f"Context: {context_length} tokens")
                print(f"Pricing: ${prompt_price}/1K prompt, ${completion_price}/1K completion")
                print(f"Modalities: {model.get('modalities', [])}")
                print(f"Description: {description[:100]}...")
                print("-" * 70)
        else:
            print(f"Available OpenRouter Image Generation Models ({len(image_models)} total):")
            for model in image_models:
                print(model.get('id', 'Unknown'))
                
    except Exception as e:
        print(f"Error listing models: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate images using OpenRouter API with image generation models.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  graft.py -p "A sunset over mountains"
  echo "A futuristic city" | graft.py
  graft.py -p "Abstract art" -m google/gemini-2.5-flash-image-preview -t 0.8
  graft.py -i bottle.png -p "make the bottle green"
  graft.py -p "street scene" -o street.png
  graft.py -p "vintage car" -o - | glimpse -p "what car model is this?"
        """
    )
    
    parser.add_argument('-p', '--prompt', help='Prompt for image generation or editing')
    parser.add_argument('-i', '--image', help='Input image file for editing')
    parser.add_argument('-o', '--output', help='Output filename (default: auto-generated)')
    parser.add_argument('-m', '--model', help='Override the model specified in config')
    parser.add_argument('-t', '--temperature', type=float, help='Override the temperature setting (0.0-1.0)')
    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List all available OpenRouter image generation model names'
    )
    
    parser.add_argument(
        '--list-models-with-details',
        action='store_true',
        help='List all available OpenRouter image generation models with detailed information'
    )
    args = parser.parse_args()
    
    # Handle --list-models commands
    if args.list_models:
        list_models(detailed=False)
        sys.exit(0)
    
    if args.list_models_with_details:
        list_models(detailed=True)
        sys.exit(0)
    
    # Validate temperature if provided
    if args.temperature is not None and (args.temperature < 0.0 or args.temperature > 1.0):
        print("Error: Temperature must be between 0.0 and 1.0")
        sys.exit(1)
    
    # Load configuration
    config = GraftConfig()
    config.load_config()
    
    # Override model if specified
    if args.model:
        config.model = args.model
    
    # Override temperature if specified
    if args.temperature is not None:
        config.temperature = args.temperature
    
    # Handle stdin input - could be text prompt or binary image data
    stdin_data = None
    stdin_is_image = False
    
    if not sys.stdin.isatty():
        # Read stdin as binary first to detect image data
        stdin_data = read_stdin_binary()
        stdin_is_image = is_binary_data(stdin_data)
    
    # Get prompt text
    prompt_text = None
    if args.prompt:
        prompt_text = args.prompt
    elif stdin_data and not stdin_is_image:
        # Text data from stdin
        prompt_text = stdin_data.decode('utf-8').strip()
    
    if not prompt_text:
        print("Error: No prompt provided. Use -p or pipe text to stdin.")
        sys.exit(1)
    
    # Handle input image - from file or stdin
    input_image_path = None
    input_image_data = None
    
    if args.image:
        # Image from file
        input_image_path = args.image
        if not os.path.exists(input_image_path):
            print(f"Error: Input image file not found: {input_image_path}")
            sys.exit(1)
        
        # Check if it's a valid image file
        mime_type, _ = mimetypes.guess_type(input_image_path)
        if not mime_type or not mime_type.startswith('image/'):
            print(f"Error: File does not appear to be an image: {input_image_path}")
            sys.exit(1)
    elif stdin_is_image:
        # Image from stdin
        input_image_data = stdin_data
    
    # Set custom filename if provided
    api = GraftAPI(config)
    if args.output:
        api.custom_filename = args.output
    
    try:
        result = api.generate_image(prompt_text, input_image_path, input_image_data)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    if result:
        print(f"\n{result}")
    else:
        print("Failed to generate image.")
        sys.exit(1)


if __name__ == "__main__":
    main()
