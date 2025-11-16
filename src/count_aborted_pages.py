#!/usr/bin/env python3
"""
Script pour compter les pages avortées (skipped) dans tous les fichiers _summary.json
"""

import json
from pathlib import Path
from typing import Dict, List

def count_aborted_pages(ocr_output_dir: str = "../data/output/ocr_results") -> Dict:
    """
    Parcourt tous les dossiers d'output OCR et compte les pages avortées

    Returns:
        Dict avec les statistiques et détails
    """
    ocr_path = Path(ocr_output_dir)

    if not ocr_path.exists():
        print(f"❌ Le dossier {ocr_output_dir} n'existe pas")
        return {}

    total_aborted = 0
    total_pdfs = 0
    pdfs_with_aborted = 0
    details = []

    # Parcourir tous les sous-dossiers
    for pdf_dir in sorted(ocr_path.iterdir()):
        if not pdf_dir.is_dir():
            continue

        summary_file = pdf_dir / "_summary.json"

        if not summary_file.exists():
            continue

        total_pdfs += 1

        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)

            # Vérifier s'il y a des pages ignorées
            if "skipped_pages" in summary and summary["skipped_pages"]:
                skipped = summary["skipped_pages"]
                num_skipped = len(skipped)
                total_aborted += num_skipped
                pdfs_with_aborted += 1

                details.append({
                    "pdf_name": summary.get("pdf_name", pdf_dir.name),
                    "total_pages": summary.get("total_pages", 0),
                    "skipped_count": num_skipped,
                    "skipped_pages": skipped
                })

        except Exception as e:
            print(f"⚠️ Erreur lors de la lecture de {summary_file}: {e}")

    return {
        "total_pdfs": total_pdfs,
        "pdfs_with_aborted": pdfs_with_aborted,
        "total_aborted_pages": total_aborted,
        "details": details
    }


def display_results(results: Dict):
    """Affiche les résultats de manière formatée"""
    print("\n" + "="*70)
    print("📊 RÉCAPITULATIF DES PAGES AVORTÉES")
    print("="*70)

    print(f"\n📁 Total de PDFs traités: {results['total_pdfs']}")
    print(f"⚠️  PDFs avec pages avortées: {results['pdfs_with_aborted']}")
    print(f"❌ Total de pages avortées: {results['total_aborted_pages']}")

    if results['details']:
        print("\n" + "-"*70)
        print("DÉTAILS PAR PDF:")
        print("-"*70)

        for detail in results['details']:
            print(f"\n📄 {detail['pdf_name']}")
            print(f"   Total pages: {detail['total_pages']}")
            print(f"   Pages avortées: {detail['skipped_count']}")
            print(f"   Détails:")
            for skipped in detail['skipped_pages']:
                print(f"      - Page {skipped['page']}: {skipped['reason']}")
    else:
        print("\n✅ Aucune page avortée trouvée!")

    print("\n" + "="*70)


if __name__ == "__main__":
    results = count_aborted_pages()
    display_results(results)
