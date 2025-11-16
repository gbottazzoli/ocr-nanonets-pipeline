#!/usr/bin/env python3
"""
Script pour retraiter les pages avortées avec un timeout augmenté à 5 minutes
- Trie les PDFs par nombre de pages avortées (du plus petit au plus grand)
- Affiche des métriques en temps réel
- Met à jour les fichiers markdown et _summary.json au fur et à mesure
"""

import os
import json
import torch
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoTokenizer, AutoProcessor
import gc
from typing import List, Dict, Tuple
import re
import tempfile
import signal
from contextlib import contextmanager
from datetime import datetime


class TimeoutException(Exception):
    """Exception levée quand un timeout se produit"""
    pass


@contextmanager
def timeout_context(seconds):
    """Context manager pour ajouter un timeout à une opération"""
    def timeout_handler(signum, frame):
        raise TimeoutException(f"Operation timed out after {seconds} seconds")

    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class AbortedPagesRetry:
    def __init__(self, ocr_output_dir: str = "../data/output/ocr_results", original_pdfs_dir: str = "../data/input"):
        """Initialize the retry processor"""
        self.ocr_output_dir = Path(ocr_output_dir)
        self.original_pdfs_dir = Path(original_pdfs_dir)

        print("Loading Nanonets-OCR2-3B model...")
        model_path = 'nanonets/Nanonets-OCR2-3B'

        self.model = AutoModelForImageTextToText.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="balanced",
            low_cpu_mem_usage=True,
            offload_folder="offload",
            offload_state_dict=True,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.processor = AutoProcessor.from_pretrained(model_path)
        self.model.eval()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        print("✓ Model loaded successfully!\n")

    def get_aborted_pages_list(self) -> List[Dict]:
        """
        Parcourt tous les _summary.json et retourne la liste des pages avortées
        triée par nombre de pages avortées (croissant)
        """
        aborted_data = []

        for pdf_dir in sorted(self.ocr_output_dir.iterdir()):
            if not pdf_dir.is_dir():
                continue

            summary_file = pdf_dir / "_summary.json"
            if not summary_file.exists():
                continue

            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)

                if "skipped_pages" in summary and summary["skipped_pages"]:
                    aborted_data.append({
                        "pdf_name": summary["pdf_name"],
                        "pdf_dir": pdf_dir,
                        "summary_file": summary_file,
                        "skipped_pages": summary["skipped_pages"],
                        "count": len(summary["skipped_pages"])
                    })
            except Exception as e:
                print(f"⚠️ Erreur lors de la lecture de {summary_file}: {e}")

        # Trier par nombre de pages avortées (croissant)
        aborted_data.sort(key=lambda x: x["count"])

        return aborted_data

    def ocr_image(self, image: Image.Image, max_new_tokens: int = 2048) -> str:
        """Perform OCR on a single image"""
        with torch.no_grad():
            max_dimension = 1400
            if max(image.size) > max_dimension:
                ratio = max_dimension / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                image.save(tmp_path)

            try:
                prompt = """Extract the text from the above document as if you were reading it naturally. Return the tables in html format if present. Return the equations in LaTeX representation if present."""

                messages = [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": [
                        {"type": "image", "image": f"file://{tmp_path}"},
                        {"type": "text", "text": prompt},
                    ]},
                ]

                text = self.processor.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )

                inputs = self.processor(
                    text=[text],
                    images=[image],
                    padding=True,
                    return_tensors="pt"
                )

                output_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    num_beams=1,
                )

                generated_ids = [
                    output_ids[len(input_ids):]
                    for input_ids, output_ids in zip(inputs['input_ids'], output_ids)
                ]

                output_text = self.processor.batch_decode(
                    generated_ids,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=True
                )

                result = output_text[0]

            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()

            return result

    def find_and_update_markdown(self, pdf_dir: Path, page_num: int, ocr_text: str, pdf_name: str) -> bool:
        """
        Trouve le fichier markdown qui contient cette page et le met à jour
        Returns True si succès, False sinon
        """
        # Chercher tous les fichiers markdown
        md_files = [f for f in pdf_dir.glob("*.md") if not f.name.startswith("_")]

        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Chercher si cette page est dans ce fichier
                # Format: ## Page X ou [SKIPPED: OCR timeout...]
                page_marker = f"## Page {page_num}"

                if page_marker in content:
                    # Trouver la section de cette page
                    lines = content.split('\n')
                    new_lines = []
                    in_target_page = False
                    replaced = False

                    for i, line in enumerate(lines):
                        if line.strip() == page_marker:
                            in_target_page = True
                            new_lines.append(line)
                            # Chercher la ligne suivante qui contient SKIPPED ou le contenu
                            if i + 1 < len(lines):
                                next_line = lines[i + 1]
                                if '[SKIPPED:' in next_line or '[ERROR:' in next_line:
                                    # Remplacer par le nouveau texte OCR
                                    new_lines.append(ocr_text)
                                    replaced = True
                                    # Sauter la ligne SKIPPED
                                    continue
                        elif in_target_page and line.startswith('## Page '):
                            # Nouvelle page, on n'est plus dans la page cible
                            in_target_page = False
                            new_lines.append(line)
                        elif not (in_target_page and '[SKIPPED:' in line):
                            new_lines.append(line)

                    if replaced:
                        # Écrire le fichier modifié
                        with open(md_file, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(new_lines))
                        return True

            except Exception as e:
                print(f"    ⚠️ Erreur lors de la mise à jour de {md_file.name}: {e}")

        return False

    def update_summary_json(self, summary_file: Path, page_num: int):
        """Retire la page du champ skipped_pages dans le _summary.json"""
        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)

            if "skipped_pages" in summary:
                # Filtrer pour retirer cette page
                summary["skipped_pages"] = [
                    p for p in summary["skipped_pages"]
                    if p["page"] != page_num
                ]

                # Si plus de pages skipped, retirer la clé
                if not summary["skipped_pages"]:
                    del summary["skipped_pages"]

            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)

            return True
        except Exception as e:
            print(f"    ⚠️ Erreur lors de la mise à jour de {summary_file}: {e}")
            return False

    def retry_single_page(self, pdf_path: Path, page_num: int, timeout: int = 300) -> Tuple[bool, str]:
        """
        Retente l'OCR sur une seule page avec un timeout augmenté
        Returns: (success, ocr_text)
        """
        try:
            # Convertir uniquement la page spécifique (page_num est 1-indexed)
            images = convert_from_path(str(pdf_path), dpi=150, first_page=page_num, last_page=page_num)

            if not images:
                return False, f"[ERROR: Could not extract page {page_num}]"

            image = images[0]

            # Tenter l'OCR avec timeout
            try:
                with timeout_context(timeout):
                    result = self.ocr_image(image)
                    return True, result
            except TimeoutException:
                return False, f"[SKIPPED: OCR timeout after {timeout}s]"
            except Exception as e:
                return False, f"[ERROR: {e}]"
            finally:
                del image
                gc.collect()

        except Exception as e:
            return False, f"[ERROR: {e}]"

    def process_all_aborted_pages(self, timeout: int = 300):
        """
        Traite toutes les pages avortées avec le nouveau timeout
        """
        aborted_data = self.get_aborted_pages_list()

        if not aborted_data:
            print("✅ Aucune page avortée à retraiter!")
            return

        # Calculer le total de pages à traiter
        total_pages = sum(data["count"] for data in aborted_data)

        print("="*80)
        print(f"📊 RETRAITEMENT DES PAGES AVORTÉES")
        print("="*80)
        print(f"PDFs à traiter: {len(aborted_data)}")
        print(f"Pages à retraiter: {total_pages}")
        print(f"Timeout: {timeout}s ({timeout//60} minutes)")
        print("="*80)
        print()

        processed_count = 0
        success_count = 0
        failed_count = 0

        for pdf_idx, data in enumerate(aborted_data, 1):
            pdf_name = data["pdf_name"]
            pdf_dir = data["pdf_dir"]
            summary_file = data["summary_file"]
            skipped_pages = data["skipped_pages"]

            # Trouver le PDF original
            pdf_path = self.original_pdfs_dir / f"{pdf_name}.pdf"

            if not pdf_path.exists():
                print(f"❌ [{pdf_idx}/{len(aborted_data)}] PDF non trouvé: {pdf_path}")
                failed_count += len(skipped_pages)
                processed_count += len(skipped_pages)
                continue

            print(f"\n{'─'*80}")
            print(f"📄 [{pdf_idx}/{len(aborted_data)}] {pdf_name}")
            print(f"   Pages à retraiter: {len(skipped_pages)}")
            print(f"{'─'*80}")

            for page_idx, skipped_info in enumerate(skipped_pages, 1):
                page_num = skipped_info["page"]
                processed_count += 1

                start_time = datetime.now()
                print(f"\n   [{processed_count}/{total_pages}] Page {page_num}/{page_idx} sur {len(skipped_pages)}... ", end='', flush=True)

                success, ocr_text = self.retry_single_page(pdf_path, page_num, timeout)

                elapsed = (datetime.now() - start_time).total_seconds()

                if success:
                    print(f"✓ OK ({elapsed:.1f}s)")
                    print(f"      Extracted {len(ocr_text)} characters")

                    # Mettre à jour le markdown
                    if self.find_and_update_markdown(pdf_dir, page_num, ocr_text, pdf_name):
                        print(f"      ✓ Markdown mis à jour")

                    # Mettre à jour le summary.json
                    if self.update_summary_json(summary_file, page_num):
                        print(f"      ✓ Summary JSON mis à jour")

                    success_count += 1
                else:
                    print(f"✗ ÉCHEC ({elapsed:.1f}s)")
                    print(f"      Raison: {ocr_text}")
                    failed_count += 1

                # Libérer la mémoire
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()

        # Résumé final
        print("\n" + "="*80)
        print("📊 RÉSUMÉ FINAL")
        print("="*80)
        print(f"✓ Pages réussies: {success_count}/{total_pages}")
        print(f"✗ Pages échouées: {failed_count}/{total_pages}")
        print(f"📈 Taux de succès: {success_count/total_pages*100:.1f}%")
        print("="*80)


if __name__ == "__main__":
    processor = AbortedPagesRetry()
    processor.process_all_aborted_pages(timeout=300)  # 5 minutes
