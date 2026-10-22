#!/data/data/com.termux/files/usr/bin/bash

set -eu

PROJECT="$HOME/dcim_calibration"
OUTPUT="$HOME/storage/shared/Download"
STAGE="$HOME/dcim_chatgpt_source_pack"

if [ ! -d "$PROJECT" ]; then
    echo "ERROR: Project directory not found: $PROJECT"
    exit 1
fi

mkdir -p "$OUTPUT"
rm -rf "$STAGE"
mkdir -p "$STAGE/source" "$STAGE/docs"

cd "$PROJECT"

# Include Python source files.
find . -maxdepth 1 -type f -name '*.py' \
    ! -name '*bak*' \
    -exec cp -t "$STAGE/source" {} +

# Include XML camera profiles.
find . -maxdepth 1 -type f -name '*.xml' \
    -exec cp -t "$STAGE/source" {} +

# Include Markdown documentation.
find . -maxdepth 1 -type f -name '*.md' \
    -exec cp -t "$STAGE/docs" {} +

# Create a source inventory.
{
    echo "DCIM Calibration - LXX521 IMX682"
    echo "Generated: $(date)"
    echo
    echo "Python, XML and Markdown source files included."
    echo "Original files remain unchanged."
    echo
    echo "PYTHON FILES"
    find "$STAGE/source" -maxdepth 1 -type f -name '*.py' -printf '%f\n' 2>/dev/null || true
    echo
    echo "XML PROFILES"
    find "$STAGE/source" -maxdepth 1 -type f -name '*.xml' -printf '%f\n' 2>/dev/null || true
    echo
    echo "DOCUMENTATION"
    find "$STAGE/docs" -maxdepth 1 -type f -name '*.md' -printf '%f\n' 2>/dev/null || true
} > "$STAGE/PROJECT_INVENTORY.txt"

# Create the upload archive.
ARCHIVE="$OUTPUT/DCIM_Calibration_ChatGPT_Source.zip"

rm -f "$ARCHIVE"

cd "$STAGE"
zip -qr "$ARCHIVE" source docs PROJECT_INVENTORY.txt

echo
echo "=========================================="
echo "ChatGPT source package created successfully"
echo "=========================================="
echo "Archive: $ARCHIVE"
ls -lh "$ARCHIVE"
echo
echo "Review the archive before uploading it."
