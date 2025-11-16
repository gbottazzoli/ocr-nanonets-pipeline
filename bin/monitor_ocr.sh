#!/bin/bash
# Script de monitoring du traitement OCR

clear
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        Monitoring OCR - Nanonets-OCR2-3B                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Fonction pour afficher une section
section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# 1. Statut Processus
section "📊 STATUT PROCESSUS"
if pgrep -f "ocr_nanonets_pausable.py" > /dev/null; then
    PID=$(pgrep -f "ocr_nanonets_pausable.py")
    echo "✅ Processus actif (PID: $PID)"

    # Temps d'exécution
    ps -p $PID -o etime= | xargs -I {} echo "   Uptime: {}"

    # Utilisation CPU/RAM
    ps -p $PID -o %cpu,%mem,rss | tail -1 | awk '{printf "   CPU: %s%%  |  RAM: %s%% (%d MB)\n", $1, $2, $3/1024}'
else
    echo "❌ Processus non actif"
    echo ""
    echo "Pour démarrer: ./START_OCR.sh"
    exit 1
fi

# 2. Progression PDFs
section "📁 PROGRESSION PDFs"
total=$(ls ../data/input/*.pdf 2>/dev/null | wc -l)
completed=$(ls -d ../data/output/ocr_results/*/ 2>/dev/null | wc -l)
remaining=$((total - completed))
percent=$((completed * 100 / total))

echo "   Total:      $total PDFs"
echo "   Complétés:  $completed PDFs"
echo "   Restants:   $remaining PDFs"
echo "   Progression: [$percent%] $(printf '█%.0s' $(seq 1 $((percent/2))))$(printf '░%.0s' $(seq 1 $((50-percent/2))))"

# Temps estimé
if [ $completed -gt 0 ]; then
    uptime_sec=$(ps -p $PID -o etimes= | xargs)
    if [ ! -z "$uptime_sec" ] && [ $uptime_sec -gt 0 ]; then
        time_per_pdf=$((uptime_sec / completed))
        eta_sec=$((time_per_pdf * remaining))
        eta_hours=$((eta_sec / 3600))
        eta_mins=$(((eta_sec % 3600) / 60))
        echo "   ETA:        ~${eta_hours}h ${eta_mins}m"
    fi
fi

# 3. PDF en cours
section "📄 PDF EN COURS"
current_pdf=$(tail -100 ../logs/ocr_production.log 2>/dev/null | grep "Processing:" | tail -1 | sed 's/.*Processing: //')
if [ ! -z "$current_pdf" ]; then
    echo "   Fichier: $current_pdf"

    # Progression pages
    page_current=$(tail -100 ../logs/ocr_production.log 2>/dev/null | grep "Processing page" | tail -1 | sed 's/.*Processing page //' | cut -d'/' -f1)
    page_total=$(tail -100 ../logs/ocr_production.log 2>/dev/null | grep "Processing page" | tail -1 | sed 's/.*Processing page //' | cut -d'/' -f2 | cut -d'.' -f1)

    if [ ! -z "$page_current" ] && [ ! -z "$page_total" ]; then
        page_percent=$((page_current * 100 / page_total))
        echo "   Pages:   $page_current / $page_total [$page_percent%]"
    fi
else
    echo "   Initialisation..."
fi

# 4. GPU
section "🎮 GPU STATUS"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits | \
    awk -F', ' '{
        printf "   GPU:         %s\n", $1
        printf "   Utilisation: %s%%\n", $2
        printf "   VRAM:        %s / %s MB (%d%%)\n", $3, $4, ($3*100/$4)
        printf "   Température: %s°C\n", $5
    }'
else
    echo "   nvidia-smi non disponible"
fi

# 5. Dernières pages traitées
section "📝 DERNIÈRES PAGES TRAITÉES"
tail -20 ../logs/ocr_production.log 2>/dev/null | grep "Extracted\|TIMEOUT\|Saved document" | tail -5 | \
while read line; do
    if [[ $line == *"TIMEOUT"* ]]; then
        echo "   ⏱️  $(echo $line | sed 's/.*⏱️  //')"
    elif [[ $line == *"Extracted"* ]]; then
        echo "   ✓ $(echo $line | sed 's/.*  //')"
    elif [[ $line == *"Saved"* ]]; then
        echo "   💾 $(echo $line | sed 's/.*→ //')"
    fi
done

# 6. Erreurs/Timeouts
section "⚠️  ERREURS & TIMEOUTS"
timeouts=$(grep -c "TIMEOUT" ../logs/ocr_production.log 2>/dev/null || echo 0)
errors=$(grep -c "ERROR" ../logs/ocr_production.log 2>/dev/null || echo 0)
echo "   Timeouts: $timeouts pages"
echo "   Erreurs:  $errors"

if [ $timeouts -gt 0 ]; then
    timeout_percent=$((timeouts * 100 / (completed * 50)))  # Approximation 50 pages/PDF
    if [ $timeout_percent -gt 20 ]; then
        echo "   ⚠️  Taux élevé de timeouts (>${timeout_percent}%)"
    fi
fi

# 7. Statistiques Output
section "💾 FICHIERS GÉNÉRÉS"
md_files=$(find ../data/output/ocr_results -name "*.md" -not -name "_*" 2>/dev/null | wc -l)
json_files=$(find ../data/output/ocr_results -name "_summary.json" 2>/dev/null | wc -l)
output_size=$(du -sh ../data/output/ocr_results 2>/dev/null | cut -f1)
echo "   Documents:  $md_files fichiers .md"
echo "   Summaries:  $json_files fichiers .json"
echo "   Taille:     $output_size"

# 8. Commandes utiles
section "🔧 COMMANDES UTILES"
echo "   tail -f ../logs/ocr_production.log  # Logs temps réel"
echo "   watch -n 5 nvidia-smi                # GPU en continu"
echo "   ./monitor_ocr.sh                     # Rafraîchir ce dashboard"
echo "   kill $PID                            # Arrêter le processus"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Dernière mise à jour: $(date '+%Y-%m-%d %H:%M:%S')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
