# Guide d'utilisation - OCR Nanonets

## Démarrage rapide

### Lancer le traitement complet

```bash
cd bin
./START_OCR.sh
```

### Lancer en mode interactif (recommandé)

```bash
cd bin
./run_pausable.sh
```

Le mode pausable permet de :
- Voir le résultat après chaque PDF
- Vérifier la qualité de l'OCR
- Décider de continuer ou arrêter
- Estimer le temps restant

---

## Commandes principales

### Scripts shell (depuis `bin/`)

| Commande | Description | Usage |
|----------|-------------|-------|
| `./START_OCR.sh` | **Production** - Traitement complet automatisé | Lancer et laisser tourner |
| `./run_pausable.sh` | **Interactif** - Pause après chaque PDF | Contrôle manuel |
| `./run_resume.sh` | **Reprise** - Reprendre après interruption | Après Ctrl+C |
| `./run_test.sh` | **Test** - Traiter un seul PDF | Validation rapide |
| `./monitor_ocr.sh` | **Surveillance** - Dashboard temps réel | Monitoring |

### Scripts Python (depuis `src/`)

| Commande | Description |
|----------|-------------|
| `python3 ocr_nanonets_pausable.py` | Script principal avec toutes les options |
| `python3 count_aborted_pages.py` | Compter les pages non traitées |
| `python3 retry_aborted_pages.py` | Retraiter les pages ayant échoué |

---

## Options de ligne de commande

```bash
cd src
python3 ocr_nanonets_pausable.py [OPTIONS]

Options disponibles :
  --input-dir PATH       Dossier contenant les PDFs
                         Défaut: ../data/input

  --output-dir PATH      Dossier de sortie
                         Défaut: ../data/output/ocr_results

  --dpi NUMBER          DPI pour conversion PDF → images
                         Défaut: 150
                         Plus bas = moins de mémoire
                         Plus haut = meilleure qualité

  --single-pdf PATH     Traiter un seul PDF
                         Exemple: --single-pdf "../data/input/R1048-13C-29913-23516.pdf"

  --pause-after-each    Pause interactive après chaque PDF
                         Permet de vérifier et continuer manuellement

  --ocr-timeout SECONDS Timeout par page en secondes
                         Défaut: 120 (2 minutes)
                         Augmenter pour pages complexes
```

---

## Exemples d'utilisation

### 1. Traitement standard

```bash
cd bin
./START_OCR.sh
```

Traite tous les PDFs avec :
- DPI: 150
- Timeout: 180s par page
- Reprise automatique
- Logs dans `logs/ocr_production.log`

### 2. Mode interactif

```bash
cd bin
./run_pausable.sh
```

Après chaque PDF, affiche :
- Temps écoulé
- Documents trouvés
- Pages traitées
- Choix : continuer (O) ou arrêter (N)

### 3. Test rapide

```bash
cd bin
./run_test.sh
```

Traite le PDF `R1048-13C-29913-23516.pdf` pour validation.

### 4. Traiter un PDF spécifique

```bash
cd src
python3 ocr_nanonets_pausable.py \
  --single-pdf "../data/input/R1049-13C-38006-23516.pdf"
```

### 5. Réduire la mémoire (DPI bas)

```bash
cd src
python3 ocr_nanonets_pausable.py \
  --dpi 100 \
  --ocr-timeout 90
```

DPI plus bas :
- ✅ Moins de mémoire GPU
- ✅ Traitement plus rapide
- ⚠️ Qualité OCR peut diminuer

### 6. Pages complexes (timeout étendu)

```bash
cd src
python3 ocr_nanonets_pausable.py \
  --ocr-timeout 300
```

Timeout 5 minutes pour pages très complexes.

### 7. Reprendre après interruption

```bash
cd bin
./run_resume.sh
```

Ou simplement relancer :
```bash
./START_OCR.sh  # Reprend automatiquement
```

La reprise fonctionne à 2 niveaux :
- **PDF** : Ignore les PDFs avec `_summary.json` complet
- **Page** : Continue à la page suivante dans un PDF incomplet

---

## Fonctionnalité Pause/Reprise

### Reprise automatique (PDF niveau)

Le script détecte automatiquement les PDFs déjà traités :

```
✓ R1048-13C-29913-23516.pdf déjà traité, ignoré
✓ R1048-13C-25754-23516.pdf déjà traité, ignoré
→ Traitement de R1049-13C-38006-23516.pdf...
```

**Critère** : Présence de `_summary.json` dans le dossier de sortie.

### Reprise au niveau page

Si un PDF est interrompu en cours :

```
PDF: R1049-13C-42876-23516.pdf (85 pages)
→ Pages 1-34 déjà traitées (trouvées dans les .md existants)
→ Reprise à la page 35
```

**Avantage** : Pas besoin de supprimer les dossiers incomplets !

### Mode pause interactif

Avec `--pause-after-each` ou `./run_pausable.sh` :

```
================================================
PDF traité : R1048-13C-29913-23516.pdf
================================================
Temps: 00:42:15
Documents trouvés: 8
Pages: 45

Continuer avec le prochain PDF ? (O/n)
→ O : Continue
→ N ou Ctrl+C : Arrête proprement
```

**Usage** :
- Vérifier la qualité après chaque PDF
- Estimer le temps total
- Arrêter proprement à tout moment

---

## Surveillance et monitoring

### Voir les logs en temps réel

```bash
# Logs du traitement principal
tail -f logs/ocr_production.log

# Logs de retry
tail -f logs/retry_aborted.log
```

### Dashboard de monitoring

```bash
cd bin
./monitor_ocr.sh
```

Affiche toutes les 5 secondes :
- PDFs traités / Total
- PDF en cours + progression
- GPU usage (nvidia-smi)
- Dernières erreurs
- Timeouts
- Taille des résultats

**Exemple de sortie** :
```
================================================
       MONITORING OCR - Nanonets-OCR2-3B
================================================

📊 PROGRESSION GLOBALE
   Total PDFs: 42
   Traités: 15 (35.7%)
   Restants: 27

📄 PDF EN COURS
   R1049-13C-42876-23516.pdf
   Page 45/85 (52.9%)

🖥️  GPU USAGE
   GPU 0: 7234 MiB / 8192 MiB (88%)
   Température: 72°C

⚠️  ERREURS
   Timeouts: 3 pages
   Erreurs: 0

💾 RÉSULTATS
   Taille output: 1.2 GB
```

---

## Vérifier les pages non traitées

Après traitement, certaines pages peuvent avoir timeout :

```bash
cd src
python3 count_aborted_pages.py
```

**Sortie** :
```
================================================
    RÉCAPITULATIF DES PAGES AVORTÉES
================================================

📁 Total de PDFs traités: 42
⚠️  PDFs avec pages avortées: 5
❌ Total de pages avortées: 12

DÉTAILS PAR PDF:
------------------------------------------------

📄 R1049-13C-42876-23516
   Total pages: 85
   Pages avortées: 3
   Détails:
      - Page 23: TIMEOUT (120s)
      - Page 45: TIMEOUT (120s)
      - Page 67: TIMEOUT (120s)

📄 R1050-13C-58219-23516
   Total pages: 102
   Pages avortées: 9
   Détails:
      - Page 12: TIMEOUT (120s)
      ...
```

---

## Retraiter les pages échouées

Pour retraiter avec timeout étendu (5 minutes) :

```bash
cd src
python3 retry_aborted_pages.py
```

**Fonctionnement** :
1. Scanne tous les `_summary.json`
2. Identifie les pages avec timeout
3. Trie par nombre de pages échouées (moins → plus)
4. Retraite avec timeout 300s
5. Met à jour les .md et _summary.json

**Surveillance du retry** :
```bash
cd bin
./monitor_retry.sh
```

---

## Workflow complet recommandé

### Première exécution

```bash
# Terminal 1 : Lancer le traitement
cd bin
./START_OCR.sh

# Terminal 2 : Surveiller
cd bin
./monitor_ocr.sh
```

### Après traitement

```bash
# 1. Vérifier les pages non traitées
cd src
python3 count_aborted_pages.py

# 2. S'il y a des pages avortées, les retraiter
python3 retry_aborted_pages.py

# 3. Re-vérifier
python3 count_aborted_pages.py
```

### En cas d'interruption

```bash
# Option 1 : Relancer directement
cd bin
./START_OCR.sh  # Reprise auto

# Option 2 : Script de reprise dédié
./run_resume.sh
```

---

## Résultats et structure de sortie

### Organisation des fichiers

```
data/output/ocr_results/
├── R1048-13C-29913-23516/
│   ├── R1048-13C-29913-23516_doc01.md
│   ├── R1048-13C-29913-23516_doc02.md
│   ├── R1048-13C-29913-23516_doc03.md
│   └── _summary.json
└── R1049-13C-38006-23516/
    └── ...
```

**Un dossier par PDF** : `{nom_pdf}/`
**Un fichier par document détecté** : `{nom_pdf}_doc01.md`, `_doc02.md`, etc.
**Métadonnées** : `_summary.json`

### Contenu d'un fichier Markdown

```markdown
# Document 1 (Pages 1-5)

## Page 1

[Texte OCR de la page 1]

---

## Page 2

[Texte OCR de la page 2]

---

...
```

### Contenu de `_summary.json`

```json
{
  "pdf_name": "R1048-13C-29913-23516",
  "total_pages": 45,
  "documents_found": 8,
  "output_directory": "data/output/ocr_results/R1048-13C-29913-23516",
  "skipped_pages": [
    {"page": 23, "reason": "TIMEOUT (120s)"}
  ]
}
```

**Champs** :
- `pdf_name` : Nom du PDF sans extension
- `total_pages` : Nombre total de pages
- `documents_found` : Nombre de documents détectés
- `output_directory` : Chemin du dossier de sortie
- `skipped_pages` : Liste des pages non traitées (vide si tout OK)

---

## Astuces et bonnes pratiques

### 1. Commencer par un test

```bash
cd bin
./run_test.sh
```

Vérifie que tout fonctionne avant de lancer le traitement complet.

### 2. Utiliser le mode interactif au début

```bash
./run_pausable.sh
```

Permet d'estimer le temps par PDF et vérifier la qualité.

### 3. Surveiller la première heure

Lancer `./monitor_ocr.sh` pendant la première heure pour :
- Vérifier l'usage GPU
- Détecter des problèmes rapidement
- Estimer le temps total

### 4. Planifier pour la nuit

Le traitement complet prend ~24-32 heures :
```bash
# Lancer le soir
cd bin
./START_OCR.sh

# Vérifier le lendemain
python3 ../src/count_aborted_pages.py
```

### 5. Gérer les interruptions

Le système est conçu pour les interruptions :
- Ctrl+C à tout moment = OK
- Coupure de courant = OK
- Relancer le script = Reprend automatiquement

---

## Raccourcis utiles

```bash
# Alias à ajouter dans ~/.bashrc
alias ocr-start='cd ~/PycharmProjects/nanosetTests/bin && ./START_OCR.sh'
alias ocr-monitor='cd ~/PycharmProjects/nanosetTests/bin && ./monitor_ocr.sh'
alias ocr-check='cd ~/PycharmProjects/nanosetTests/src && python3 count_aborted_pages.py'
alias ocr-retry='cd ~/PycharmProjects/nanosetTests/src && python3 retry_aborted_pages.py'
```

Après redémarrage du terminal :
```bash
ocr-start    # Lancer
ocr-monitor  # Surveiller
ocr-check    # Vérifier
ocr-retry    # Retraiter
```

---

**Pour plus de détails** : Consultez `TROUBLESHOOTING.md` pour la résolution de problèmes.
