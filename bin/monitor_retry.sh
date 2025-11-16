#!/bin/bash
# Script pour monitorer la progression du retraitement

echo "═══════════════════════════════════════════════════════════════"
echo "📊 MONITORING DU RETRAITEMENT DES PAGES AVORTÉES"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Compter les succès et échecs dans le log
successes=$(grep -c "✓ OK" ../logs/retry_aborted.log 2>/dev/null || echo 0)
failures=$(grep -c "✗ ÉCHEC" ../logs/retry_aborted.log 2>/dev/null || echo 0)
total_processed=$((successes + failures))

echo "✓ Succès: $successes"
echo "✗ Échecs: $failures"
echo "📈 Total traité: $total_processed / 67"
echo ""

if [ $total_processed -gt 0 ]; then
    success_rate=$(awk "BEGIN {printf \"%.1f\", ($successes/$total_processed)*100}")
    echo "Taux de succès: $success_rate%"
    echo ""
fi

echo "───────────────────────────────────────────────────────────────"
echo "Dernières lignes du log:"
echo "───────────────────────────────────────────────────────────────"
tail -15 ../logs/retry_aborted.log 2>/dev/null || echo "Aucun log disponible"
