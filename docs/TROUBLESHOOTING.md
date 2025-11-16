# Dépannage et résolution de problèmes

## Table des matières

1. [Problèmes de mémoire GPU](#problèmes-de-mémoire-gpu)
2. [Pages qui timeout](#pages-qui-timeout)
3. [Traitement interrompu](#traitement-interrompu)
4. [Erreurs de modèle](#erreurs-de-modèle)
5. [Problèmes de performance](#problèmes-de-performance)
6. [Logs et monitoring](#logs-et-monitoring)
7. [Déploiement en production](#déploiement-en-production)

---

## Problèmes de mémoire GPU

### Symptôme : OutOfMemoryError (OOM)

```
RuntimeError: CUDA out of memory. Tried to allocate X MiB
```

### Solutions

#### Solution 1 : Réduire le DPI

```bash
cd src
python3 ocr_nanonets_pausable.py --dpi 100
```

Impact :
- ✅ Réduit la mémoire de ~40%
- ✅ Traitement plus rapide
- ⚠️ Qualité OCR peut légèrement diminuer

DPI recommandés :
- **150** : Qualité optimale (défaut)
- **120** : Bon compromis
- **100** : Économie maximale
- **80** : Dernière option (texte petit)

#### Solution 2 : Utiliser CPU offload

```bash
cd bin
./run_full_ocr.sh  # Utilise la variante cpu_offload
```

Ou manuellement :
```bash
cd src
python3 ocr_nanonets_cpu_offload.py
```

**Comment ça marche** :
- Décharge certaines parties du modèle vers la RAM
- Plus lent (~30% plus lent)
- Très stable même avec 6GB VRAM

#### Solution 3 : Fermer les applications GPU

```bash
# Vérifier les processus utilisant le GPU
nvidia-smi

# Tuer un processus spécifique
kill -9 [PID]
```

Applications à fermer :
- Navigateurs (Chrome, Firefox)
- Autres modèles ML
- Jeux
- Compositeurs graphiques intensifs

#### Solution 4 : Nettoyer le cache

```bash
cd src
python3 -c "import torch; torch.cuda.empty_cache(); print('Cache cleared')"
```

### Symptôme : Ralentissement progressif

Le traitement ralentit au fil du temps.

**Cause** : Accumulation de cache mémoire

**Solution** : Redémarrer périodiquement
```bash
# Arrêter proprement
Ctrl+C

# Relancer (reprise auto)
cd bin
./START_OCR.sh
```

Le script reprend automatiquement là où il s'est arrêté.

---

## Pages qui timeout

### Symptôme : Pages ignorées

```
⚠️ TIMEOUT page 23 après 120 secondes
→ Page ignorée, passage à la suivante
```

### Comprendre les timeouts

**Pourquoi ?**
- Pages très complexes (tableaux, images)
- Texte manuscrit difficile
- Qualité PDF faible
- Charge GPU élevée

**Impact** :
- Page ignorée = pas de texte extrait
- Traitement continue avec la page suivante
- Informé dans `_summary.json`

### Compter les pages timeout

```bash
cd src
python3 count_aborted_pages.py
```

**Sortie** :
```
📁 Total de PDFs traités: 42
⚠️  PDFs avec pages avortées: 5
❌ Total de pages avortées: 12
```

### Retraiter avec timeout étendu

```bash
cd src
python3 retry_aborted_pages.py
```

**Paramètres du retry** :
- Timeout : **300 secondes** (5 minutes vs 2 minutes)
- Ordre : PDFs avec le moins d'échecs d'abord
- Mise à jour : Met à jour les .md et _summary.json automatiquement

**Surveiller le retry** :
```bash
cd bin
./monitor_retry.sh
```

### Ajuster le timeout dès le départ

Si vous savez que les PDFs sont complexes :

```bash
cd src
python3 ocr_nanonets_pausable.py --ocr-timeout 300
```

**Compromis** :
- ⏱️ Traitement plus long
- ✅ Moins de pages ignorées

---

## Traitement interrompu

### Interruption volontaire (Ctrl+C)

**Statut** : ✅ Normal, géré automatiquement

**Pour reprendre** :
```bash
cd bin
./START_OCR.sh  # Reprend automatiquement
```

ou

```bash
./run_resume.sh  # Script dédié
```

### Interruption système (crash, coupure)

**Statut** : ✅ Géré par la reprise automatique

**Ce qui est préservé** :
- PDFs complètement traités (avec `_summary.json`)
- Pages déjà traitées dans un PDF incomplet

**Ce qui est perdu** :
- Page en cours de traitement (sera retraitée)

**Pour reprendre** :
```bash
cd bin
./START_OCR.sh
```

### Vérifier l'état après interruption

```bash
cd src

# Voir combien de PDFs traités
ls ../data/output/ocr_results/ | wc -l

# Vérifier les pages timeout
python3 count_aborted_pages.py
```

### Supprimer un PDF incomplet (optionnel)

Si un PDF semble corrompu :

```bash
# Identifier le PDF problématique
cd data/output/ocr_results/
ls -lt  # Trier par date

# Supprimer le dossier
rm -rf R1049-13C-XXXXX-23516/

# Relancer (retraitera ce PDF)
cd ../../bin
./START_OCR.sh
```

---

## Erreurs de modèle

### Erreur : Modèle non trouvé

```
OSError: nanonets/Nanonets-OCR2-3B is not a local folder and is not a valid model identifier
```

**Cause** : Première utilisation, modèle pas encore téléchargé

**Solution** : Vérifier la connexion internet
```bash
# Le modèle (~6GB) sera téléchargé automatiquement
cd src
python3 ocr_nanonets_pausable.py --single-pdf "../data/input/[un_pdf].pdf"
```

**Téléchargement manuel** (si échec) :
```bash
python3 -c "from transformers import AutoModelForImageTextToText; \
AutoModelForImageTextToText.from_pretrained('nanonets/Nanonets-OCR2-3B', trust_remote_code=True)"
```

### Erreur : CUDA non disponible

```
AssertionError: CUDA is not available
```

**Vérifications** :
```bash
# 1. Vérifier CUDA
nvidia-smi

# 2. Vérifier PyTorch
python3 -c "import torch; print(torch.cuda.is_available())"
```

**Si False** :
```bash
# Réinstaller PyTorch avec support CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

---

## Problèmes de performance

### Traitement très lent

**Symptômes** :
- Plus de 60 minutes par PDF
- GPU usage < 50%

**Diagnostics** :

```bash
# Vérifier GPU
nvidia-smi

# Vérifier si CPU offload est utilisé
ps aux | grep ocr_nanonets
```

**Solutions** :

1. **Vérifier le script utilisé**
```bash
# Rapide (recommandé)
python3 ocr_nanonets_pausable.py

# Lent (CPU offload)
python3 ocr_nanonets_cpu_offload.py
```

2. **Augmenter le DPI peut aider**
```bash
# Si GPU sous-utilisé, augmenter DPI
python3 ocr_nanonets_pausable.py --dpi 180
```

3. **Vérifier thermal throttling**
```bash
nvidia-smi --query-gpu=temperature.gpu --format=csv

# Si > 80°C, améliorer le refroidissement
```

### PDF très long (>200 pages)

**Problème** : Risque de timeout global

**Solution** : Traiter par batch manuel
```bash
# Diviser le PDF en plusieurs fichiers
# Puis traiter séparément

cd src
python3 ocr_nanonets_pausable.py --single-pdf "../data/input/part1.pdf"
python3 ocr_nanonets_pausable.py --single-pdf "../data/input/part2.pdf"
```

---

## Logs et monitoring

### Localisation des logs

```
logs/
├── ocr_processing.log    # Traitement général
├── ocr_production.log    # Production (START_OCR.sh)
└── retry_aborted.log     # Retraitement
```

### Voir les logs en temps réel

```bash
# Logs principaux
tail -f logs/ocr_production.log

# Filtrer les erreurs
tail -f logs/ocr_production.log | grep -i error

# Filtrer les timeouts
tail -f logs/ocr_production.log | grep -i timeout
```

### Dashboard de monitoring

```bash
cd bin
./monitor_ocr.sh
```

**Affiche** :
- Progression globale (PDFs traités/total)
- PDF en cours + page actuelle
- Usage GPU en temps réel
- Erreurs et timeouts
- Taille des résultats
- Estimation temps restant

**Rafraîchissement** : Toutes les 5 secondes

### Logs personnalisés

Rediriger vers un fichier spécifique :

```bash
cd src
python3 ocr_nanonets_pausable.py 2>&1 | tee ../logs/custom_run.log
```

### Analyser les logs

**Compter les erreurs** :
```bash
grep -c "ERROR" logs/ocr_production.log
```

**Compter les timeouts** :
```bash
grep -c "TIMEOUT" logs/ocr_production.log
```

**Voir les dernières erreurs** :
```bash
grep "ERROR" logs/ocr_production.log | tail -20
```

**Extraire les pages timeout** :
```bash
grep "TIMEOUT" logs/ocr_production.log | grep "page"
```

---

## Déploiement en production

### Configuration recommandée

**Matériel** :
- GPU : NVIDIA 8GB+ VRAM (RTX 3060, RTX 4060, etc.)
- RAM : 16GB minimum
- Stockage : SSD pour meilleure performance I/O
- Refroidissement : Bon système de ventilation

**Logiciel** :
- OS : Linux (Ubuntu 20.04+, Fedora 38+)
- Python : 3.10+
- CUDA : 11.8 ou 12.1
- Drivers : Dernière version NVIDIA

### Lancement en production

#### Option 1 : Screen session

```bash
# Créer une session screen
screen -S ocr_production

# Dans la session
cd /path/to/nanosetTests/bin
./START_OCR.sh

# Détacher : Ctrl+A puis D
# Rattacher plus tard : screen -r ocr_production
```

#### Option 2 : Tmux

```bash
# Créer session tmux
tmux new -s ocr_production

# Dans la session
cd /path/to/nanosetTests/bin
./START_OCR.sh

# Détacher : Ctrl+B puis D
# Rattacher : tmux attach -t ocr_production
```

#### Option 3 : Service systemd

Créer `/etc/systemd/system/ocr-nanonets.service` :

```ini
[Unit]
Description=OCR Nanonets Processing
After=network.target

[Service]
Type=simple
User=steeven
WorkingDirectory=/home/steeven/PycharmProjects/nanosetTests/bin
ExecStart=/home/steeven/PycharmProjects/nanosetTests/bin/START_OCR.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Puis :
```bash
sudo systemctl daemon-reload
sudo systemctl start ocr-nanonets
sudo systemctl enable ocr-nanonets  # Démarrage auto

# Vérifier
sudo systemctl status ocr-nanonets

# Logs
sudo journalctl -u ocr-nanonets -f
```

### Surveillance en production

#### Monitoring GPU

```bash
# Dashboard GPU temps réel
watch -n 1 nvidia-smi

# Ou avec monitoring dédié
cd bin
./monitor_ocr.sh
```

#### Alertes par email (optionnel)

Script de surveillance avec alerte :

```bash
#!/bin/bash
# monitor_with_alert.sh

while true; do
  # Vérifier si le processus tourne
  if ! pgrep -f "ocr_nanonets_pausable.py" > /dev/null; then
    echo "OCR process stopped!" | mail -s "OCR Alert" user@example.com
    break
  fi

  # Vérifier GPU
  gpu_usage=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)
  if [ "$gpu_usage" -lt 10 ]; then
    echo "GPU usage low: $gpu_usage%" | mail -s "OCR Alert" user@example.com
  fi

  sleep 300  # Vérifier toutes les 5 minutes
done
```

### Rotation des logs

Pour éviter les logs trop gros :

```bash
# Créer /etc/logrotate.d/ocr-nanonets
/home/steeven/PycharmProjects/nanosetTests/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### Sauvegarde automatique

```bash
#!/bin/bash
# backup_results.sh

DATE=$(date +%Y%m%d)
SOURCE="/home/steeven/PycharmProjects/nanosetTests/data/output/ocr_results"
DEST="/backup/ocr_results_$DATE"

rsync -av --progress "$SOURCE" "$DEST"
echo "Backup completed: $DEST"
```

Ajouter dans crontab :
```bash
crontab -e

# Sauvegarde quotidienne à 2h du matin
0 2 * * * /path/to/backup_results.sh
```

### Performance tuning

#### 1. Optimiser I/O disque

```bash
# Utiliser tmpfs pour fichiers temporaires (si RAM disponible)
sudo mount -t tmpfs -o size=4G tmpfs /tmp/ocr_temp

# Modifier le script pour utiliser ce dossier
export TMPDIR=/tmp/ocr_temp
```

#### 2. Nice priority

```bash
# Réduire la priorité CPU si besoin
nice -n 10 ./START_OCR.sh
```

#### 3. GPU power limit

```bash
# Augmenter la limite de puissance (si supporté)
sudo nvidia-smi -pl 250  # 250W

# Vérifier
nvidia-smi -q -d POWER
```

### Checklist de déploiement

- [ ] Environnement Python configuré
- [ ] Modèle téléchargé (`~6GB`)
- [ ] Logs configurés avec rotation
- [ ] Monitoring en place
- [ ] Session persistante (screen/tmux/systemd)
- [ ] Sauvegarde automatique configurée
- [ ] Test sur un PDF validé
- [ ] Documentation accessible à l'équipe

---

## FAQ - Questions fréquentes

### Combien de temps pour traiter 42 PDFs ?

**Estimation** : 24-32 heures

**Détail** :
- PDF simple (20 pages) : ~15-20 min
- PDF moyen (50 pages) : ~35-45 min
- PDF complexe (100 pages) : ~60-90 min

**Facteurs** :
- Complexité du texte
- Qualité du PDF
- DPI utilisé
- Charge GPU

### Puis-je traiter plusieurs PDFs en parallèle ?

**Non recommandé** avec 8GB VRAM.

**Raison** : Le modèle consomme ~6-7GB seul.

**Alternative** : Si vous avez 2 GPUs :
```bash
# GPU 0
CUDA_VISIBLE_DEVICES=0 python3 ocr_nanonets_pausable.py --input-dir batch1/

# GPU 1
CUDA_VISIBLE_DEVICES=1 python3 ocr_nanonets_pausable.py --input-dir batch2/
```

### Les résultats sont-ils déterministes ?

**Oui**, le même PDF donnera le même résultat.

**Sauf** :
- Si le modèle est mis à jour
- Si les paramètres changent (DPI, etc.)

### Puis-je modifier les patterns de détection de documents ?

**Oui**, dans `src/ocr_nanonets_pausable.py` :

```python
def detect_document_boundary(self, text: str, page_num: int) -> bool:
    # Modifier ces patterns
    date_pattern = r'\d{2}/\d{2}/\d{4}'
    reference_pattern = r'R\d{4}-13C-'
    # ...
```

### Comment exporter en JSON au lieu de Markdown ?

Modifier la fonction `save_document()` dans le script Python, ou utiliser un script de conversion :

```bash
# Exemple : Convertir tous les .md en .json
for dir in data/output/ocr_results/*/; do
  # Script de conversion personnalisé
  python3 convert_md_to_json.py "$dir"
done
```

---

**Besoin d'aide ?** Consultez `GUIDE_PROJET.md` pour plus de détails sur le fonctionnement interne.
