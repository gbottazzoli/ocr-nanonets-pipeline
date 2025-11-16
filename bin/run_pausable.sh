#!/bin/bash
# Run OCR with PAUSE after each PDF

echo "=========================================="
echo "Nanonets OCR - Mode PAUSABLE"
echo "=========================================="
echo ""
echo "Ce script va traiter les PDFs UN PAR UN"
echo "Après chaque PDF, vous pourrez choisir de:"
echo "  - Continuer au prochain PDF"
echo "  - Faire une pause et arrêter"
echo ""
echo "Si vous arrêtez, vous pourrez reprendre plus tard."
echo "Les PDFs déjà traités seront automatiquement sautés."
echo ""
echo "Log: ../logs/ocr_processing.log"
echo "Output: ../data/output/ocr_results/"
echo ""
read -p "Appuyez sur ENTRÉE pour démarrer..."
echo ""

mkdir -p ../data/output/ocr_results offload

python3 ../src/ocr_nanonets_pausable.py \
    --input-dir ../data/input \
    --output-dir ../data/output/ocr_results \
    --dpi 120 \
    --pause-after-each \
    2>&1 | tee ../logs/ocr_processing.log
