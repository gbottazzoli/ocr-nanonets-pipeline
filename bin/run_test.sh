#!/bin/bash
# Test script to process a single PDF first

echo "Testing OCR on a single PDF..."
python3 ../src/ocr_processor.py --single-pdf "../data/input/R1048-13C-29913-23516.pdf" --output-dir "ocr_output_test"

echo ""
echo "Test complete! Check ocr_output_test/ folder for results"
