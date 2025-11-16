#!/bin/bash
# Process all PDFs in the download_original folder

echo "Starting OCR processing for all PDFs..."
echo "This will process PDFs from ../data/input/ - this may take several hours"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    python3 ../src/ocr_processor.py --input-dir ../data/input --output-dir ../data/output/ocr_results
    echo ""
    echo "Processing complete!"
    echo "Results saved in ../data/output/ocr_results/"
fi
