# Guide du Projet OCR Nanonets

## Vue d'ensemble

Ce projet est un pipeline OCR (reconnaissance optique de caractères) pour traiter des documents PDF historiques en utilisant le modèle d'apprentissage profond **Nanonets-OCR2-3B**. Il extrait le texte des PDFs et le sauvegarde en format Markdown avec détection automatique des frontières de documents.

---

## Prérequis

### Environnement système
- **GPU**: NVIDIA avec au moins 8 GB de VRAM (optimisé pour cette configuration)
- **RAM**: 16 GB recommandé
- **Système d'exploitation**: Linux (testé sur Fedora)
- **Python**: Python 3.13+
- **Conda**: Pour la gestion de l'environnement virtuel

### Dépendances Python

Installez les dépendances avec :
```bash
pip install -r requirements.txt
```

**Liste des dépendances** :
- `torch>=2.0.0` - Framework d'apprentissage profond
- `torchvision>=0.15.0` - Utilitaires vision par ordinateur
- `transformers>=4.30.0` - Bibliothèque HuggingFace pour modèles pré-entraînés
- `pdf2image>=1.16.0` - Conversion PDF vers images
- `Pillow>=9.0.0` - Traitement d'images
- `accelerate>=0.20.0` - Optimisation distribuée
- `bitsandbytes>=0.41.0` - Quantification et optimisation mémoire

### Modèle OCR

Le modèle **Nanonets-OCR2-3B** sera téléchargé automatiquement depuis HuggingFace Hub lors de la première exécution (~6 GB).

---

## Scripts principaux et leurs fonctions

### Scripts Python

#### 1. `ocr_nanonets_pausable.py` ⭐ **SCRIPT PRINCIPAL**
**Fonction** : Processeur OCR principal avec capacités avancées

**Caractéristiques** :
- ✅ Système de pause/reprise entre PDFs
- ✅ Détection automatique de timeout (120 secondes par page)
- ✅ Reprise automatique : ignore les PDFs déjà traités
- ✅ Reprise au niveau page : ignore les pages déjà traitées
- ✅ Détection des frontières de documents dans un PDF
- ✅ Traitement page par page pour économiser la mémoire

**Sortie** :
- Fichiers Markdown (un par document détecté)
- Fichier `_summary.json` avec métadonnées de traitement

---

#### 2. `ocr_processor.py`
**Fonction** : Classe de base pour le traitement OCR

**Caractéristiques** :
- Implémentation de base du processeur OCR
- Chargement du modèle avec optimisation FP16 pour GPU 8GB
- Pipeline standard de traitement

**Usage** : Classe fondamentale utilisée par les autres scripts

---

#### 3. `ocr_nanonets_cpu_offload.py`
**Fonction** : Variante avec déchargement CPU agressif

**Caractéristiques** :
- Utilise `device_map="balanced"` pour économiser la VRAM
- Décharge certains composants du modèle vers la RAM CPU
- Plus lent mais plus stable si contraintes mémoire GPU

**Quand l'utiliser** : Quand le script principal rencontre des erreurs de mémoire

---

#### 4. `count_aborted_pages.py` 🔍
**Fonction** : Utilitaire d'analyse des pages ignorées

**Caractéristiques** :
- Scanne tous les fichiers `_summary.json`
- Compte les pages qui ont timeout
- Génère des statistiques sur les échecs de traitement

**Usage** :
```bash
python count_aborted_pages.py
```

**Sortie** : Rapport console avec liste des PDFs ayant des pages non traitées

---

#### 5. `retry_aborted_pages.py` 🔄
**Fonction** : Retraitement des pages ayant échoué

**Caractéristiques** :
- Retraite les pages qui ont timeout lors du premier passage
- Augmente le timeout à **5 minutes** (vs 120 secondes par défaut)
- Trie les PDFs par nombre de pages échouées (les plus faciles d'abord)
- Met à jour les fichiers Markdown et JSON au fur et à mesure

**Usage** :
```bash
python retry_aborted_pages.py
```

---

### Scripts Shell

#### `START_OCR.sh` 🚀 **POINT D'ENTRÉE PRINCIPAL**
**Fonction** : Lance le traitement complet automatisé

**Usage** :
```bash
./START_OCR.sh
```

---

#### `run_pausable.sh`
**Fonction** : Mode interactif avec pause entre chaque PDF

**Usage** :
```bash
./run_pausable.sh
```

---

#### `run_resume.sh`
**Fonction** : Reprend un traitement interrompu

**Usage** :
```bash
./run_resume.sh
```

---

#### `run_test.sh`
**Fonction** : Test rapide sur un seul PDF

**Usage** :
```bash
./run_test.sh
```

---

#### `run_full_ocr.sh`
**Fonction** : Traitement complet sans pause

**Usage** :
```bash
./run_full_ocr.sh
```

---

#### `monitor_ocr.sh` 📊
**Fonction** : Surveillance en temps réel du traitement

**Usage** :
```bash
./monitor_ocr.sh
```

---

#### `monitor_retry.sh`
**Fonction** : Surveillance des opérations de retry

**Usage** :
```bash
./monitor_retry.sh
```

---

#### `activate_env.sh`
**Fonction** : Active l'environnement conda

**Usage** :
```bash
source activate_env.sh
```

---

## Structure des dossiers

### Dossiers sources

#### `download_original/` 📂 **DONNÉES D'ENTRÉE**
**Contenu** : 42 fichiers PDF historiques (902 MB)

**Séries de documents** :
- `R1048-13C-*.pdf` - 11 PDFs
- `R1049-13C-*.pdf` - 26 PDFs
- `R1050-13C-*.pdf` - 4 PDFs
- `R1049-13C-Casuals-23516.pdf` - 1 PDF spécial

**Choix de structure** : Organisation par série de référence pour faciliter le traitement par lot

---

#### `ocr_output/` 📄 **DONNÉES DE SORTIE**
**Contenu** : Résultats de l'OCR pour 43 PDFs

**Organisation** :
```
ocr_output/
├── R1048-13C-23516-23516/          # Un dossier par PDF
│   ├── R1048-13C-23516-23516_doc01.md    # Document 1
│   ├── R1048-13C-23516-23516_doc02.md    # Document 2
│   ├── ...
│   └── _summary.json                     # Métadonnées
```

**Choix de structure** :
- **Un dossier par PDF** : Facilite l'organisation et la recherche
- **Documents séparés** : Chaque document détecté a son propre fichier Markdown
- **Numérotation séquentielle** : `_doc01`, `_doc02`, etc.
- **Fichier summary JSON** : Contient les métadonnées (nombre de pages, documents trouvés, pages ignorées)

---

### Fichiers de logs

| Fichier | Description |
|---------|-------------|
| `ocr_processing.log` | Journal principal du traitement |
| `ocr_production.log` | Journal de la run de production |
| `retry_aborted.log` | Journal des opérations de retry |

**Choix de logging** : Logs séparés pour faciliter le débogage et la surveillance

---

## Workflow recommandé

### 1. Premier traitement
```bash
./START_OCR.sh
```

### 2. Vérifier les pages non traitées
```bash
python count_aborted_pages.py
```

### 3. Retraiter les pages échouées (si nécessaire)
```bash
python retry_aborted_pages.py
```

### 4. Surveiller le traitement en temps réel
```bash
# Terminal 1
./START_OCR.sh

# Terminal 2
./monitor_ocr.sh
```

---

## Choix techniques effectués

### 1. **Optimisation mémoire GPU (8GB VRAM)**
- Utilisation de **FP16** (demi-précision) au lieu de FP32
- Traitement **page par page** pour éviter les pics mémoire
- Libération explicite de la mémoire après chaque page

### 2. **Système de reprise multi-niveau**
- **Niveau PDF** : Les PDFs déjà traités sont ignorés
- **Niveau page** : Les pages déjà traitées sont ignorées
- **Raison** : Permet de reprendre après interruption sans re-traiter

### 3. **Timeout par page (120 secondes)**
- Évite de bloquer indéfiniment sur des pages complexes
- Les pages ignorées peuvent être retraitées avec timeout étendu
- **Raison** : Meilleur compromis entre complétude et temps de traitement

### 4. **Détection automatique de documents**
- Utilise des patterns regex pour détecter les séparateurs de documents
- Patterns recherchés :
  - Titres en majuscules centrés
  - Dates au format spécifique
  - Numéros de référence
- **Raison** : Un PDF peut contenir plusieurs documents distincts

### 5. **Format de sortie Markdown**
- Format texte simple et portable
- Compatible avec de nombreux outils
- Facilite la recherche et l'édition
- **Raison** : Meilleur format pour archivage et traitement ultérieur

### 6. **Organisation par dossier PDF**
- Chaque PDF a son propre dossier de sortie
- **Raison** : Facilite la traçabilité et l'organisation des résultats

---

## Statistiques du projet

| Métrique | Valeur |
|----------|--------|
| **PDFs traités** | 42 |
| **Documents extraits** | ~665 |
| **Pages totales** | ~2500+ |
| **Taille des PDFs** | 902 MB |
| **Taille des résultats** | 4.1 MB |
| **Format de sortie** | Markdown + JSON |

---

## Résolution de problèmes

### Erreur de mémoire GPU
**Solution** : Utilisez `ocr_nanonets_cpu_offload.py` au lieu du script principal

### Pages qui timeout
**Solution** : Lancez `retry_aborted_pages.py` après le traitement principal

### Traitement interrompu
**Solution** : Relancez simplement le script, la reprise est automatique

---

## Documentation supplémentaire

Pour plus de détails, consultez :
- `README.md` - Guide principal du projet
- `USAGE_GUIDE.md` - Guide d'utilisation complet
- `GUIDE_PAUSE.md` - Documentation sur le système de pause
- `MONITORING.md` - Guide de surveillance
- `COMMANDES_OCR.md` - Référence des commandes

---

**Version** : 1.0
**Dernière mise à jour** : Novembre 2025
**Statut** : Production ✅
