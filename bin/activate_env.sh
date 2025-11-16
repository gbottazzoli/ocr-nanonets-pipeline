#!/bin/bash
# Script pour activer l'environnement conda ocr_nanonets

echo "Activation de l'environnement conda 'ocr_nanonets'..."
echo ""
echo "Pour activer manuellement:"
echo "  conda activate ocr_nanonets"
echo ""
echo "Pour lancer l'OCR:"
echo "  python3 ../src/ocr_nanonets_pausable.py --input-dir ../data/input"
echo ""

conda activate ocr_nanonets
