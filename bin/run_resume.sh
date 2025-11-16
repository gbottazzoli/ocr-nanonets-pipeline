#!/bin/bash
# Resume OCR processing - automatically skips completed PDFs

echo "=========================================="
echo "Nanonets OCR - REPRENDRE le traitement"
echo "=========================================="
echo ""
echo "Ce script va:"
echo "  1. Vérifier quels PDFs sont déjà traités"
echo "  2. Sauter automatiquement les PDFs complétés"
echo "  3. Continuer avec les PDFs restants"
echo ""

# Count already processed
processed=$(ls -1 ../data/output/ocr_results 2>/dev/null | wc -l)
total=$(ls -1 ../data/input/*.pdf 2>/dev/null | wc -l)
remaining=$((total - processed))

echo "État actuel:"
echo "  ✓ PDFs déjà traités: $processed"
echo "  ⏳ PDFs restants: $remaining"
echo ""

if [ $remaining -eq 0 ]; then
    echo "✅ Tous les PDFs sont déjà traités!"
    exit 0
fi

read -p "Continuer avec les $remaining PDFs restants? (O/n): " response
if [[ "$response" =~ ^[Nn] ]]; then
    echo "Annulé."
    exit 0
fi

echo ""
echo "Reprise du traitement..."
echo ""

mkdir -p ../data/output/ocr_results offload

python3 ../src/ocr_nanonets_pausable.py \
    --input-dir ../data/input \
    --output-dir ../data/output/ocr_results \
    --dpi 120 \
    2>&1 | tee -a ../logs/ocr_processing.log
