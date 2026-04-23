#!/bin/bash

# Exit on error
set -e

echo "Installing Graft..."

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed. Please install Python 3 first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install requirements
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create wrapper script in ~/.local/bin
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

WRAPPER_PATH="$INSTALL_DIR/graft"

echo "Creating executable wrapper at $WRAPPER_PATH..."
cat > "$WRAPPER_PATH" << EOF
#!/bin/bash
"$DIR/venv/bin/python" "$DIR/graft.py" "\$@"
EOF

chmod +x "$WRAPPER_PATH"

echo ""
echo "✅ Installation complete!"
echo ""
echo "Graft has been installed to $WRAPPER_PATH"
echo ""
echo "Please ensure that ~/.local/bin is in your PATH."
echo "You can test it by running: graft -h"
