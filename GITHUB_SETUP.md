# Guide de publication sur GitHub

## ✅ Préparation terminée

Le projet est prêt pour GitHub :
- ✅ Git initialisé
- ✅ .gitignore configuré (données exclues)
- ✅ Commit initial créé
- ✅ Dossiers vides préservés avec .gitkeep

## 📦 Ce qui sera publié

### Fichiers inclus (25 fichiers - ~4096 lignes)

```
✅ bin/          → 9 scripts shell
✅ src/          → 5 scripts Python
✅ docs/         → 4 fichiers documentation
✅ data/input/   → .gitkeep (dossier vide)
✅ data/output/  → .gitkeep (dossier vide)
✅ logs/         → .gitkeep (dossier vide)
✅ README.md
✅ QUICKSTART.md
✅ requirements.txt
✅ .gitignore
```

### Fichiers exclus (via .gitignore)

```
❌ data/input/*.pdf        → Vos 42 PDFs (~902 MB)
❌ data/output/ocr_results/ → Résultats OCR (~4.1 MB)
❌ logs/*.log              → Fichiers de logs
❌ __pycache__/            → Cache Python
❌ .idea/, .obsidian/      → Fichiers IDE
❌ .claude/                → Configuration locale
```

**Taille du repo GitHub** : ~200 KB (au lieu de ~1 GB avec les données)

---

## 🚀 Étapes pour publier sur GitHub

### 1. Créer un nouveau dépôt sur GitHub

**Option A : Via l'interface web**

1. Allez sur https://github.com/new
2. Remplissez :
   - **Repository name** : `ocr-nanonets-pipeline` (ou autre nom)
   - **Description** : `Pipeline OCR pour documents PDF avec Nanonets-OCR2-3B - GPU optimisé`
   - **Visibilité** : Public ou Private (votre choix)
   - ⚠️ **NE PAS** cocher "Initialize with README" (on a déjà un README)
   - ⚠️ **NE PAS** ajouter .gitignore ou license (on les a déjà)
3. Cliquer sur **"Create repository"**

**Option B : Via GitHub CLI (si installé)**

```bash
gh repo create ocr-nanonets-pipeline --public --description "Pipeline OCR pour documents PDF avec Nanonets-OCR2-3B" --source=. --remote=origin
```

### 2. Lier votre dépôt local à GitHub

GitHub vous donnera des commandes. Utilisez celles pour un **dépôt existant** :

```bash
# Remplacez USERNAME par votre nom d'utilisateur GitHub
git remote add origin https://github.com/USERNAME/ocr-nanonets-pipeline.git

# Ou avec SSH (si configuré)
git remote add origin git@github.com:USERNAME/ocr-nanonets-pipeline.git
```

### 3. Pousser le code sur GitHub

```bash
# Pousser la branche main
git push -u origin main
```

**Si vous utilisez une authentification** :
- **Token** : GitHub vous demandera votre Personal Access Token
- **SSH** : Assurez-vous que votre clé SSH est configurée

---

## 🔑 Authentification GitHub

### Créer un Personal Access Token (si nécessaire)

1. Allez sur https://github.com/settings/tokens
2. Cliquez sur **"Generate new token"** → **"Generate new token (classic)"**
3. Donnez un nom : `OCR Pipeline Upload`
4. Sélectionnez les permissions :
   - ✅ `repo` (tous les sous-items)
5. Cliquez sur **"Generate token"**
6. **Copiez le token** (vous ne le reverrez plus!)
7. Utilisez-le comme mot de passe lors du `git push`

### Ou configurer SSH (recommandé)

```bash
# Générer une clé SSH (si vous n'en avez pas)
ssh-keygen -t ed25519 -C "claritYe@proton.me"

# Copier la clé publique
cat ~/.ssh/id_ed25519.pub

# Ajouter cette clé sur GitHub :
# https://github.com/settings/ssh/new
```

---

## 📋 Commandes complètes (copier-coller)

```bash
# 1. Vérifier l'état actuel
git status
git log --oneline

# 2. Ajouter le remote GitHub (remplacez USERNAME et REPO_NAME)
git remote add origin https://github.com/USERNAME/REPO_NAME.git

# 3. Vérifier le remote
git remote -v

# 4. Pousser sur GitHub
git push -u origin main

# 5. Vérifier que tout est en ligne
# Allez sur https://github.com/USERNAME/REPO_NAME
```

---

## 🎯 Utiliser le projet sur une autre machine

Une fois publié sur GitHub, n'importe qui peut l'utiliser :

### Cloner le projet

```bash
git clone https://github.com/USERNAME/ocr-nanonets-pipeline.git
cd ocr-nanonets-pipeline
```

### Installer les dépendances

```bash
# Créer un environnement virtuel
conda create -n ocr_nanonets python=3.13
conda activate ocr_nanonets

# Installer les dépendances
pip install -r requirements.txt
```

### Ajouter vos PDFs

```bash
# Copier vos PDFs dans le dossier input
cp /path/to/your/pdfs/*.pdf data/input/
```

### Lancer le traitement

```bash
cd bin
./START_OCR.sh
```

Le modèle Nanonets-OCR2-3B (~6GB) sera téléchargé automatiquement au premier lancement.

---

## 🔄 Mettre à jour le projet sur GitHub

### Après modifications locales

```bash
# 1. Voir les modifications
git status

# 2. Ajouter les fichiers modifiés
git add .

# 3. Créer un commit
git commit -m "Description de vos changements"

# 4. Pousser sur GitHub
git push
```

### Exemples de commits

```bash
# Amélioration de script
git commit -m "Amélioration: Augmenter timeout par défaut à 180s"

# Correction de bug
git commit -m "Fix: Correction gestion des pages vides"

# Documentation
git commit -m "Docs: Ajout exemples DPI personnalisé"

# Nouvelle fonctionnalité
git commit -m "Feature: Support format TIFF en entrée"
```

---

## 📝 Créer une belle page GitHub

### Ajouter des badges (optionnel)

Ajoutez en haut du README.md :

```markdown
# OCR Nanonets - Pipeline de traitement PDF historiques

![Python](https://img.shields.io/badge/python-3.13+-blue.svg)
![CUDA](https://img.shields.io/badge/CUDA-11.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-production-success.svg)
```

### Ajouter une LICENSE (recommandé)

```bash
# Créer un fichier LICENSE
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 [Votre Nom]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# Ajouter et commiter
git add LICENSE
git commit -m "Add MIT License"
git push
```

### Ajouter des topics GitHub

Sur votre repo GitHub, cliquez sur ⚙️ à côté de "About", puis ajoutez :
- `ocr`
- `pdf-processing`
- `nanonets`
- `gpu`
- `cuda`
- `python`
- `machine-learning`
- `document-processing`

---

## ✅ Checklist finale

Avant de publier, vérifiez :

- [ ] Le README.md est clair et complet
- [ ] Le .gitignore exclut bien les données sensibles
- [ ] Les scripts ont des permissions d'exécution (`chmod +x bin/*.sh`)
- [ ] requirements.txt est à jour
- [ ] La documentation est accessible (docs/)
- [ ] Aucune donnée personnelle dans le code
- [ ] Aucun mot de passe ou token dans les fichiers

---

## 🎉 Vous êtes prêt!

**Commandes finales** :

```bash
# Créer le repo sur GitHub (via web ou CLI)
# Puis :

git remote add origin https://github.com/USERNAME/REPO_NAME.git
git push -u origin main

# Vérifier sur https://github.com/USERNAME/REPO_NAME
```

**Partager votre projet** :
- URL du repo : `https://github.com/USERNAME/REPO_NAME`
- Clone commande : `git clone https://github.com/USERNAME/REPO_NAME.git`

---

**Questions ?** Consultez la [documentation GitHub](https://docs.github.com/fr/get-started/quickstart/create-a-repo)
