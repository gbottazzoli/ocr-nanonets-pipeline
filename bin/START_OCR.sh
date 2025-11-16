#!/bin/bash
# Script pour lancer le traitement OCR complet

echo "=================================================="
echo "  Lancement Traitement OCR - Nanonets-OCR2-3B"
echo "=================================================="
echo ""

# Activation environnement
echo "🔧 Activation environnement conda..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate ocr_nanonets

# Vérification
echo "✓ Python: $(python --version)"
echo "✓ Environnement: $CONDA_DEFAULT_ENV"
echo ""

# Comptage PDFs
total=$(ls ../data/input/*.pdf 2>/dev/null | wc -l)
processed=$(ls -d ../data/output/ocr_results/*/ 2>/dev/null | wc -l)
remaining=$((total - processed))

echo "📊 Statistiques:"
echo "   Total PDFs: $total"
echo "   Déjà traités: $processed"
echo "   Restants: $remaining"
echo ""

# Confirmation
read -p "Lancer le traitement de $remaining PDFs? (o/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Oo]$ ]]; then
    echo "Annulé."
    exit 1
fi

echo ""
echo "🚀 Lancement du traitement..."
echo "   Log: logs/ocr_production.log"
echo "   Monitoring: tail -f logs/ocr_production.log"
echo ""
echo "Appuyez sur Ctrl+C dans les 3 secondes pour annuler..."
sleep 3

# Lancement en arrière-plan
nohup python3 ../src/ocr_nanonets_pausable.py \
    --input-dir ../data/input \
    --output-dir ../data/output/ocr_results \
    --dpi 150 \
    --ocr-timeout 180 \
    > ../logs/ocr_production.log 2>&1 &

PID=$!
echo ""
echo "=================================================="
echo "✅ Traitement lancé!"
echo "=================================================="
echo "   PID: $PID"
echo "   Log: logs/ocr_production.log"
echo ""
echo "📊 Monitoring:"
echo "   tail -f logs/ocr_production.log     # Logs en temps réel"
echo "   watch -n 5 nvidia-smi                # GPU usage"
echo "   bin/monitor_ocr.sh                   # Dashboard complet"
echo ""
echo "⏹️  Arrêter:"
echo "   kill $PID"
echo ""
echo "Estimation: ~24-32 heures pour $remaining PDFs"
echo "=================================================="
