# Nana Banana

A collection of AI-powered command-line tools for text analysis and image generation using OpenRouter API.

## Tools

- **glean.py** - Text analysis and question answering
- **graft.py** - Image generation and editing  
- **google.py** - Direct Google AI API integration (experimental)

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

Both tools require OpenRouter API configuration. Create configuration files in your home directory:

### For glean.py (text analysis)
Create `~/.glean_cfg`:
```ini
[openrouter]
api_key = your_openrouter_api_key_here
model = anthropic/claude-3.5-sonnet
temperature = 0.7
```

### For graft.py (image generation)
Create `~/.graft_cfg`:
```ini
[openrouter]
api_key = your_openrouter_api_key_here
model = google/gemini-2.5-flash-image-preview
temperature = 0.4
```

## Usage

### Graft - Image Generation & Editing

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

# List available models
python3 graft.py --list-models
```

### Glean - Text Analysis

**Analyze text:**
```bash
python3 glean.py -p "Summarize this text" -f document.txt
echo "What is AI?" | python3 glean.py
```

**Advanced features:**
```bash
# Override model
python3 glean.py -p "Analyze sentiment" -f text.txt -m anthropic/claude-3.5-sonnet

# List available models
python3 glean.py --list-models
```

## Features

### Graft (Image Generation)
- ✅ Generate images from text prompts
- ✅ Edit existing images with text instructions
- ✅ Support for file input (`-i image.png`)
- ✅ Support for piped image data (`curl | graft`)
- ✅ Multiple image formats (PNG, JPEG, GIF, WebP, BMP)
- ✅ Base64 image handling
- ✅ Automatic filename generation with timestamps

### Glean (Text Analysis)
- ✅ Text analysis and question answering
- ✅ File input support
- ✅ Stdin text processing
- ✅ Multiple AI models via OpenRouter
- ✅ Configurable temperature and prompts

## Project Structure

```
nana-banana/
├── glean.py          # Text analysis tool
├── graft.py          # Image generation tool
├── google.py         # Direct Google AI integration
├── requirements.txt  # Python dependencies
├── venv/            # Virtual environment
├── .gitignore       # Git ignore patterns
└── README.md        # This documentation
```

## Supported Models

**Image Generation (graft.py):**
- `google/gemini-2.5-flash-image-preview` (default)
- Other OpenRouter models with image output capability

**Text Analysis (glean.py):**
- `anthropic/claude-3.5-sonnet` (default)
- `openai/gpt-4o`
- `meta-llama/llama-3.1-405b-instruct`
- Many other OpenRouter models

Use `--list-models` with either tool to see all available options.
