# Graft

A command-line tool for AI-powered image generation and editing using OpenRouter API.

Sister projects: [Glean](https://github.com/u1i/glean) (text analysis) and [Glimpse](https://github.com/u1i/glimpse) (image analysis)

## Installation

1. Clone this repository
2. Set up a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Create `~/.graft_cfg` in your home directory:

```ini
[openrouter]
api_key = your_openrouter_api_key_here
model = google/gemini-2.5-flash-image-preview
temperature = 0.4
```

## Usage

**Generate new images:**
```bash
python3 graft.py -p "A sunset over mountains"
echo "A futuristic city" | python3 graft.py
```

**Edit existing images:**
```bash
# Edit image from file
python3 graft.py -i photo.jpg -p "make it black and white"

# Edit image from URL via curl
curl https://example.com/image.png | python3 graft.py -p "turn it into an orange logo"
```

**Advanced options:**
```bash
# Override model and temperature
python3 graft.py -p "Abstract art" -m google/gemini-2.5-flash-image-preview -t 0.8

# Specify output filename
python3 graft.py -p "street scene" -o street.png

# Multiple images saved as street.png, street_2.png, street_3.png, etc.
python3 graft.py -p "create 3 variations of a street scene" -o street.png

# Output to stdout for piping (only first image if multiple are generated)
python3 graft.py -p "vintage car" -o - | glimpse -p "what car model is this?"

# Process multiple prompts from a file (handles prompts with spaces)
while read p; do graft -p "$p" < /dev/null; done < prompts.txt

# List available models
python3 graft.py --list-models
```

## Features

- ✅ Generate images from text prompts
- ✅ Edit existing images with text instructions
- ✅ Support for file input (`-i image.png`)
- ✅ Support for piped image data (`curl | graft`)
- ✅ Custom output filename (`-o filename.png`)
- ✅ Output to stdout for piping (`-o -`)
- ✅ Multiple output images (saved as `image.png`, `image_2.png`, etc.)
- ✅ Multiple image formats (PNG, JPEG, GIF, WebP, BMP)
- ✅ Base64 image handling
- ✅ Automatic filename generation with timestamps

## Supported Models

- `google/gemini-2.5-flash-image-preview` (default)
- Other OpenRouter models with image output capability

Use `--list-models` to see all available options.
