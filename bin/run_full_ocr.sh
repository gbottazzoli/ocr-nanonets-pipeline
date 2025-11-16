#!/bin/bash
# Production script to process all PDFs with Nanonets OCR
# With CPU offloading for 8GB GPU

echo "=========================================="
echo "Nanonets OCR - Batch Processing"
echo "=========================================="
echo ""
echo "This will process PDFs from ../data/input/"
echo "Estimated time: 3-5 days"
echo ""
echo "Progress will be logged to: ../logs/ocr_processing.log"
echo "Output will be saved to: ../data/output/ocr_results/"
echo ""
echo "You can monitor progress with:"
echo "  tail -f ../logs/ocr_processing.log"
echo ""
echo "Or check GPU usage:"
echo "  watch -n 5 nvidia-smi"
echo ""
read -p "Press ENTER to start, or Ctrl+C to cancel..."
echo ""

# Create output directory
mkdir -p ../data/output/ocr_results
mkdir -p offload

# Run the OCR processor
python3 ../src/ocr_nanonets_cpu_offload.py \
    --input-dir ../data/input \
    --output-dir ../data/output/ocr_results \
    --dpi 120 \
    2>&1 | tee ../logs/ocr_processing.log

echo ""
echo "=========================================="
echo "Processing Complete!"
echo "=========================================="
echo "Check ../data/output/ocr_results/ for results"
echo "Log saved to: ../logs/ocr_processing.log"
