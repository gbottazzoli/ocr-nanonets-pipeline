#!/usr/bin/env python3
"""
OCR processor with PAUSE capability and RESUME support
- Can be resumed later - automatically skips already processed PDFs
- Can resume interrupted PDF processing by detecting already processed pages
- Includes page-level timeout (default 120s) to avoid blocking on problematic pages
- Logs skipped pages (due to timeout) in _summary.json
"""

import os
import json
import torch
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoTokenizer, AutoProcessor
import gc
from typing import List, Tuple, Set, Dict, Optional
import re
import tempfile
import sys
import signal
from contextlib import contextmanager


class TimeoutException(Exception):
    """Exception levée quand un timeout se produit"""
    pass


@contextmanager
def timeout_context(seconds):
    """Context manager pour ajouter un timeout à une opération"""
    def timeout_handler(signum, frame):
        raise TimeoutException(f"Operation timed out after {seconds} seconds")

    # Set the signal handler and a timeout alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Restore the old handler and cancel the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class NanonetsOCRProcessor:
    def __init__(self, output_base_dir: str = "../data/output/ocr_results", pause_after_each: bool = False):
        """Initialize the OCR processor with Nanonets model"""
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(exist_ok=True)
        self.pause_after_each = pause_after_each

        print("Loading Nanonets-OCR2-3B model with CPU offloading...")
        print("This may be slow but will work with 8GB GPU")
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

        print("Model loaded successfully with CPU offloading!")
        print(f"Output directory: {self.output_base_dir}")

    def pdf_to_images(self, pdf_path: str, dpi: int = 150) -> List[Image.Image]:
        """Convert PDF to images"""
        print(f"Converting PDF to images: {Path(pdf_path).name}")
        images = convert_from_path(pdf_path, dpi=dpi)
        print(f"Converted {len(images)} pages")
        return images

    def ocr_image(self, image: Image.Image, max_new_tokens: int = 2048) -> str:
        """Perform OCR on a single image"""
        with torch.no_grad():
            max_dimension = 1400
            if max(image.size) > max_dimension:
                ratio = max_dimension / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                print(f"  Resized image to {new_size}")

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

    def detect_document_boundary(self, current_result: str, previous_result: str = None) -> bool:
        """Detect if current page starts a new document"""
        if previous_result is None:
            return True

        lines = current_result.strip().split('\n')
        if not lines:
            return False

        first_line = lines[0].strip()

        header_patterns = [
            r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'^[A-Z]\d{4}[-\s]',
            r'^(DOCUMENT|LETTER|MEMO|REPORT)',
            r'^\d+\s+(January|February|March|April|May|June|July|August|September|October|November|December)',
        ]

        for pattern in header_patterns:
            if re.search(pattern, first_line, re.IGNORECASE):
                return True

        if 5 < len(first_line) < 60 and len(lines) > 2:
            return True

        return False

    def format_as_markdown(self, pages_data: List[Tuple[int, str]], document_num: int) -> str:
        """Format OCR results as markdown"""
        md_content = f"# Document {document_num}\n\n"
        md_content += f"Pages: {pages_data[0][0] + 1}"
        if len(pages_data) > 1:
            md_content += f" - {pages_data[-1][0] + 1}"
        md_content += f" ({len(pages_data)} page{'s' if len(pages_data) > 1 else ''})\n\n"
        md_content += "---\n\n"

        for page_num, result in pages_data:
            md_content += f"## Page {page_num + 1}\n\n"
            md_content += result + "\n\n"
            md_content += "---\n\n"

        return md_content

    def is_pdf_processed(self, pdf_path: Path) -> bool:
        """Check if PDF has already been processed"""
        pdf_output_dir = self.output_base_dir / pdf_path.stem
        summary_file = pdf_output_dir / "_summary.json"
        return summary_file.exists()

    def get_processed_pages(self, pdf_output_dir: Path) -> Set[int]:
        """Extract which pages have already been processed from existing markdown files"""
        processed_pages = set()

        if not pdf_output_dir.exists():
            return processed_pages

        # Find all markdown files (except summary)
        md_files = [f for f in pdf_output_dir.glob("*.md") if not f.name.startswith("_")]

        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract page numbers from "## Page N" markers
                page_matches = re.findall(r'^## Page (\d+)', content, re.MULTILINE)
                for match in page_matches:
                    # Convert to 0-indexed
                    processed_pages.add(int(match) - 1)

            except Exception as e:
                print(f"  Warning: Could not read {md_file.name}: {e}")

        return processed_pages

    def get_last_document_number(self, pdf_output_dir: Path) -> int:
        """Find the highest document number already created"""
        if not pdf_output_dir.exists():
            return 0

        md_files = [f for f in pdf_output_dir.glob("*.md") if not f.name.startswith("_")]

        max_doc_num = 0
        for md_file in md_files:
            # Extract document number from filename like "name_doc05.md"
            match = re.search(r'_doc(\d+)\.md$', md_file.name)
            if match:
                doc_num = int(match.group(1))
                max_doc_num = max(max_doc_num, doc_num)

        return max_doc_num

    def process_pdf(self, pdf_path: str, dpi: int = 150, ocr_timeout: int = 120) -> None:
        """Process a single PDF file with resume capability"""
        pdf_path = Path(pdf_path)
        print(f"\n{'='*60}")
        print(f"Processing: {pdf_path.name}")
        print(f"{'='*60}")

        pdf_output_dir = self.output_base_dir / pdf_path.stem
        pdf_output_dir.mkdir(exist_ok=True)

        # Check for existing progress
        processed_pages = self.get_processed_pages(pdf_output_dir)
        document_num = self.get_last_document_number(pdf_output_dir) + 1

        if processed_pages:
            print(f"  ⚡ Found existing progress: {len(processed_pages)} pages already processed")
            print(f"  ⚡ Resuming from document number {document_num}")

        images = self.pdf_to_images(str(pdf_path), dpi=dpi)

        current_document_pages = []
        previous_result = None
        skipped_pages = []  # Track pages that timed out

        for page_num, image in enumerate(images):
            # Skip already processed pages
            if page_num in processed_pages:
                print(f"\n✓ Skipping page {page_num + 1}/{len(images)} (already processed)")
                del image
                gc.collect()
                continue

            print(f"\nProcessing page {page_num + 1}/{len(images)}...")

            try:
                # Try OCR with timeout
                with timeout_context(ocr_timeout):
                    result = self.ocr_image(image)
                    print(f"  Extracted {len(result)} characters")

                is_new_doc = self.detect_document_boundary(result, previous_result)

                if is_new_doc and current_document_pages:
                    self.save_document(
                        pdf_output_dir,
                        current_document_pages,
                        document_num,
                        pdf_path.stem
                    )
                    document_num += 1
                    current_document_pages = []

                current_document_pages.append((page_num, result))
                previous_result = result

            except TimeoutException as e:
                print(f"  ⏱️ TIMEOUT on page {page_num + 1}: OCR took longer than {ocr_timeout}s - SKIPPING page")
                skipped_pages.append({
                    "page": page_num + 1,
                    "reason": f"OCR timeout after {ocr_timeout} seconds"
                })
                current_document_pages.append((page_num, f"[SKIPPED: OCR timeout after {ocr_timeout}s]"))

            except Exception as e:
                print(f"  ERROR on page {page_num + 1}: {e}")
                current_document_pages.append((page_num, f"[ERROR: {e}]"))

            del image
            gc.collect()

        if current_document_pages:
            self.save_document(
                pdf_output_dir,
                current_document_pages,
                document_num,
                pdf_path.stem
            )

        self.save_summary(pdf_output_dir, pdf_path.stem, document_num, len(images), skipped_pages)

        print(f"\nCompleted! Found {document_num} document(s) in {len(images)} pages")
        if skipped_pages:
            print(f"  ⚠️ Skipped {len(skipped_pages)} page(s) due to timeout")
        print(f"Output saved to: {pdf_output_dir}")

    def save_document(self, output_dir: Path, pages_data: List[Tuple[int, str]],
                     doc_num: int, pdf_name: str) -> None:
        """Save a single document as markdown"""
        md_content = self.format_as_markdown(pages_data, doc_num)
        output_file = output_dir / f"{pdf_name}_doc{doc_num:02d}.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"  → Saved document {doc_num} ({len(pages_data)} pages) to {output_file.name}")

    def save_summary(self, output_dir: Path, pdf_name: str,
                    num_docs: int, num_pages: int, skipped_pages: List[Dict] = None) -> None:
        """Save processing summary"""
        summary = {
            "pdf_name": pdf_name,
            "total_pages": num_pages,
            "documents_found": num_docs,
            "output_directory": str(output_dir)
        }

        if skipped_pages:
            summary["skipped_pages"] = skipped_pages

        with open(output_dir / "_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)

    def process_directory(self, input_dir: str, ocr_timeout: int = 120) -> None:
        """Process all PDFs in a directory with pause capability"""
        input_path = Path(input_dir)
        pdf_files = sorted(input_path.glob("*.pdf"))

        print(f"Found {len(pdf_files)} PDF files")

        # Check which ones are already processed
        remaining_pdfs = []
        processed_count = 0
        for pdf_file in pdf_files:
            if self.is_pdf_processed(pdf_file):
                print(f"  ✓ Already processed: {pdf_file.name}")
                processed_count += 1
            else:
                remaining_pdfs.append(pdf_file)

        if processed_count > 0:
            print(f"\n{processed_count} PDFs already processed, skipping them.")

        if not remaining_pdfs:
            print("All PDFs are already processed!")
            return

        print(f"\n{len(remaining_pdfs)} PDFs remaining to process")

        for i, pdf_file in enumerate(remaining_pdfs, 1):
            print(f"\n{'#'*60}")
            print(f"# [{i}/{len(remaining_pdfs)}] Processing: {pdf_file.name}")
            print(f"{'#'*60}")

            try:
                self.process_pdf(str(pdf_file), ocr_timeout=ocr_timeout)
            except Exception as e:
                print(f"ERROR processing {pdf_file.name}: {e}")
                continue

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()

            # PAUSE after each PDF if requested
            if self.pause_after_each and i < len(remaining_pdfs):
                print(f"\n{'='*60}")
                print(f"PDF {i}/{len(remaining_pdfs)} completed!")
                print(f"Remaining: {len(remaining_pdfs) - i} PDFs")
                print(f"{'='*60}")

                response = input("\n[C]ontinue to next PDF, [P]ause and exit? (C/p): ").strip().lower()

                if response == 'p':
                    print("\n⏸️  Processing PAUSED")
                    print(f"✓ Completed: {processed_count + i} PDFs")
                    print(f"⏳ Remaining: {len(remaining_pdfs) - i} PDFs")
                    print("\nTo resume later, run the same command again.")
                    print("Already processed PDFs will be skipped automatically.")
                    sys.exit(0)
                else:
                    print("\n▶️  Continuing to next PDF...")

        print(f"\n{'='*60}")
        print(f"All complete! Processed {len(pdf_files)} PDFs")
        print(f"Output directory: {self.output_base_dir}")
        print(f"{'='*60}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Nanonets OCR with pause capability and resume support")
    parser.add_argument("--input-dir", default="../data/input")
    parser.add_argument("--output-dir", default="../data/output/ocr_results")
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--single-pdf", type=str, default=None)
    parser.add_argument("--pause-after-each", action="store_true",
                       help="Pause after each PDF with option to continue or exit")
    parser.add_argument("--ocr-timeout", type=int, default=120,
                       help="Timeout in seconds for OCR per page (default: 120s)")

    args = parser.parse_args()

    Path("offload").mkdir(exist_ok=True)

    processor = NanonetsOCRProcessor(
        output_base_dir=args.output_dir,
        pause_after_each=args.pause_after_each
    )

    if args.single_pdf:
        processor.process_pdf(args.single_pdf, dpi=args.dpi, ocr_timeout=args.ocr_timeout)
    else:
        processor.process_directory(args.input_dir, ocr_timeout=args.ocr_timeout)


if __name__ == "__main__":
    main()
