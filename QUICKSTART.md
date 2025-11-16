# Démarrage Rapide - OCR Nanonets

## Structure du projet

```
nanosetTests/
├── bin/         → Scripts d'exécution (.sh)
├── src/         → Code source Python (.py)
├── docs/        → Documentation complète
├── logs/        → Fichiers de logs
├── data/
│   ├── input/   → PDFs à traiter (42 fichiers)
│   └── output/  → Résultats OCR
│       └── ocr_results/
└── README.md    → Documentation principale
```

## Lancement en 3 étapes

### 1. Activer l'environnement

```bash
cd bin
source activate_env.sh
```

### 2. Lancer le traitement

```bash
./START_OCR.sh
```

### 3. Surveiller (optionnel)

```bash
# Dans un autre terminal
cd bin
./monitor_ocr.sh
```

## Commandes principales

| Commande | Description |
|----------|-------------|
| `cd bin && ./START_OCR.sh` | Traitement complet automatisé |
| `cd bin && ./run_pausable.sh` | Mode interactif avec pause |
| `cd bin && ./run_test.sh` | Test sur un seul PDF |
| `cd bin && ./monitor_ocr.sh` | Dashboard de surveillance |
| `cd src && python3 count_aborted_pages.py` | Compter pages non traitées |
| `cd src && python3 retry_aborted_pages.py` | Retraiter pages échouées |

## Résultats

Les résultats sont dans `data/output/ocr_results/`:
- Un dossier par PDF
- Fichiers `.md` avec le texte extrait
- Fichier `_summary.json` avec métadonnées

## En cas de problème

1. **Erreur de mémoire GPU** → Réduire DPI: `--dpi 100`
2. **Pages timeout** → Lancer `retry_aborted_pages.py`
3. **Interruption** → Relancer le même script (reprise auto)

## Documentation

- **README.md** - Documentation complète
- **docs/GUIDE_PROJET.md** - Guide du projet
- **docs/** - Toute la documentation

---

**Aide**: Consultez `README.md` pour plus de détails
