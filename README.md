# OCR Nanonets - Pipeline de traitement PDF historiques

Pipeline OCR professionnel pour extraire le texte de documents PDF historiques utilisant le modèle **Nanonets-OCR2-3B**.

## Caractéristiques principales

- **Optimisé GPU 8GB VRAM** - Traitement efficace avec FP16
- **Reprise automatique** - Continue après interruption (niveau PDF et page)
- **Protection timeout** - Ignore les pages problématiques (défaut: 2 min)
- **Pause interactive** - Contrôle entre chaque PDF
- **Détection de documents** - Sépare automatiquement les documents dans un PDF
- **Format Markdown** - Sortie texte portable et éditable
- **Gestion mémoire** - Traitement page par page optimisé

## Exemple de résultat

### Document original → Texte extrait

<table>
<tr>
<td width="50%">

**📄 INPUT : PDF scanné**

Document historique de la Société des Nations (1922)
- Texte manuscrit et imprimé
- Qualité variable
- Format PDF ancien

</td>
<td width="50%">

**✨ OUTPUT : Texte Markdown**

```markdown
Page 1

1922
SOCIÉTÉ DES NATIONS.
LEAGUE OF NATIONS.

Classement. INTERNATIONAL BUREAUX. RIO48 REGISTRY.

Classement Document
No.        No.
13.c       23516

INTELLECTUAL CO-OPERATION

Expéditeur.
3rd Assembly
of the
League.

Date.
21 September
1922.

Sujet.
Seperanto as an Auxiliary International Language
Report submitted by the 5th Committee
to the 3rd Assembly, & Resolutions
adopted by the Assembly, 21 September
1922.
A. 81.
A. 109. (Resolution 9)
```

</td>
</tr>
</table>

**Résultat** : Texte structuré, recherchable et éditable préservant la mise en page originale.

## Structure du projet

```
nanosetTests/
├── bin/                    Scripts d'exécution (shell)
├── src/                    Scripts Python (code source)
├── docs/                   Documentation complète
├── logs/                   Fichiers de logs
├── data/
│   ├── input/             PDFs source (42 fichiers)
│   └── output/
│       └── ocr_results/   Résultats OCR (format Markdown)
├── requirements.txt       Dépendances Python
└── README.md              Ce fichier
```

## Prérequis

### Système
- **GPU**: NVIDIA avec 8GB+ VRAM
- **Python**: 3.13+
- **Conda**: Pour environnement virtuel
- **Système**: Linux (testé sur Fedora)

### Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Le modèle Nanonets-OCR2-3B (~6GB) sera téléchargé automatiquement
```

## Démarrage rapide

### 1. Traitement complet automatisé

```bash
cd bin
./START_OCR.sh
```

Ce script lance le traitement de tous les PDFs avec :
- Reprise automatique (ignore les PDFs déjà traités)
- Timeout de 180 secondes par page
- Logs dans `logs/ocr_production.log`

### 2. Mode interactif (recommandé pour débuter)

```bash
cd bin
./run_pausable.sh
```

Permet de :
- Voir le résultat après chaque PDF
- Décider de continuer ou arrêter
- Vérifier la qualité de l'OCR

### 3. Test rapide sur un PDF

```bash
cd bin
./run_test.sh
```

Traite un seul PDF pour valider la configuration.

## Utilisation avancée

### Scripts Python disponibles (dans `src/`)

| Script | Description |
|--------|-------------|
| `ocr_nanonets_pausable.py` | **Principal** - Avec pause/reprise et timeout |
| `ocr_processor.py` | Version de base |
| `ocr_nanonets_cpu_offload.py` | Variante avec déchargement CPU (si OOM) |
| `count_aborted_pages.py` | Compte les pages ignorées |
| `retry_aborted_pages.py` | Retraite les pages ayant échoué |

### Scripts shell disponibles (dans `bin/`)

| Script | Fonction |
|--------|----------|
| `START_OCR.sh` | Point d'entrée principal |
| `run_pausable.sh` | Mode interactif avec pause |
| `run_resume.sh` | Reprendre un traitement interrompu |
| `run_test.sh` | Test rapide |
| `run_full_ocr.sh` | Traitement complet sans pause |
| `monitor_ocr.sh` | Surveillance en temps réel |
| `monitor_retry.sh` | Surveillance des retries |

### Options de ligne de commande

```bash
cd src
python3 ocr_nanonets_pausable.py --help

Options:
  --input-dir         Dossier contenant les PDFs (défaut: ../data/input)
  --output-dir        Dossier de sortie (défaut: ../data/output/ocr_results)
  --dpi              DPI conversion PDF (défaut: 150)
  --single-pdf        Traiter un seul PDF
  --pause-after-each  Mode interactif
  --ocr-timeout       Timeout par page en secondes (défaut: 120)
```

### Exemples d'utilisation

```bash
cd src

# Traiter avec timeout personnalisé (5 minutes)
python3 ocr_nanonets_pausable.py --ocr-timeout 300

# Traiter un PDF spécifique
python3 ocr_nanonets_pausable.py --single-pdf "../data/input/R1048-13C-29913-23516.pdf"

# Mode interactif avec DPI réduit
python3 ocr_nanonets_pausable.py --pause-after-each --dpi 120
```

## Structure de sortie

```
data/output/ocr_results/
├── R1048-13C-29913-23516/          # Un dossier par PDF
│   ├── R1048-13C-29913-23516_doc01.md    # Document 1
│   ├── R1048-13C-29913-23516_doc02.md    # Document 2
│   ├── R1048-13C-29913-23516_doc03.md    # Document 3
│   └── _summary.json                     # Métadonnées
└── R1049-13C-38006-23516/
    └── ...
```

### Contenu des fichiers Markdown

Chaque fichier `.md` contient :
- Numéro de document et plage de pages
- Texte OCR organisé par page
- Séparateurs de pages

### Fichier `_summary.json`

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

## Workflow recommandé

### Traitement initial

```bash
# 1. Lancer le traitement
cd bin
./START_OCR.sh

# 2. Surveiller (dans un autre terminal)
cd bin
./monitor_ocr.sh

# 3. En cas d'interruption, reprendre
./run_resume.sh
```

### Vérification et retry

```bash
cd src

# 1. Compter les pages non traitées
python3 count_aborted_pages.py

# 2. Retraiter avec timeout étendu (5 min)
python3 retry_aborted_pages.py
```

## Gestion des erreurs

### Problème de mémoire GPU

**Solution 1**: Réduire le DPI
```bash
cd src
python3 ocr_nanonets_pausable.py --dpi 100
```

**Solution 2**: Utiliser la version CPU offload
```bash
cd bin
./run_full_ocr.sh  # Utilise ocr_nanonets_cpu_offload.py
```

### Pages qui timeout

Les pages complexes peuvent prendre plus de temps. Pour les retraiter :

```bash
cd src
python3 retry_aborted_pages.py
```

Ce script :
- Augmente le timeout à 5 minutes
- Traite d'abord les PDFs avec le moins de pages échouées
- Met à jour les fichiers Markdown et JSON

### Traitement interrompu

Relancez simplement le même script :

```bash
cd bin
./START_OCR.sh  # Reprend automatiquement
```

La reprise fonctionne à deux niveaux :
- **Niveau PDF**: Ignore les PDFs complètement traités
- **Niveau page**: Continue à la page suivante dans un PDF partiellement traité

## Détection de documents

Le système détecte automatiquement les séparateurs de documents dans un PDF :

**Patterns détectés** :
- En-têtes de date (ex: `22/02/2019`)
- Numéros de référence (ex: `R1048-13C-...`)
- Types de documents (ex: `LETTER`, `MEMO`)
- Titres suivis de contenu

**Résultat** : Un PDF de 100 pages peut générer 15 documents séparés.

## Surveillance

### Logs en temps réel

```bash
# Logs principaux
tail -f logs/ocr_production.log

# Logs de retry
tail -f logs/retry_aborted.log
```

### Dashboard de monitoring

```bash
cd bin
./monitor_ocr.sh
```

Affiche :
- PDFs traités / restants
- Progression actuelle
- Usage GPU
- Erreurs et timeouts
- Taille des résultats

## Documentation complète

Consultez le dossier `docs/` pour :

- **README.md** - Index et navigation de la documentation
- **GUIDE_PROJET.md** - Vue d'ensemble, prérequis, scripts, choix techniques
- **USAGE.md** - Guide d'utilisation complet avec exemples et workflows
- **TROUBLESHOOTING.md** - Résolution de problèmes, optimisation, déploiement production

## Statistiques du projet

| Métrique | Valeur |
|----------|--------|
| PDFs traités | 42 |
| Documents extraits | ~665 |
| Pages totales | ~2500+ |
| Taille entrée | 902 MB |
| Taille sortie | 4.1 MB |
| Format sortie | Markdown + JSON |
| Temps moyen | ~35-45 min/PDF |

## Support et développement

### Structure du code

- **Code source** : `src/` - Scripts Python modulaires
- **Exécutables** : `bin/` - Scripts shell pour automatisation
- **Documentation** : `docs/` - Guides complets
- **Données** : `data/` - Séparation input/output

### Contribuer

Pour modifier le code :
1. Les scripts Python sont dans `src/`
2. Les scripts shell sont dans `bin/`
3. Tester avec `bin/run_test.sh`
4. Documenter dans `docs/`

---

**Version** : 1.0
**Dernière mise à jour** : Novembre 2025
**Statut** : Production
