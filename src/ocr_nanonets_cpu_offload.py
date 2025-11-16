#!/usr/bin/env python3
"""
OCR processor for historical PDF documents using Nanonets-OCR2-3B
WITH AGGRESSIVE CPU OFFLOADING for 8GB GPU
This will be SLOWER but should work without OOM errors
"""

import os
import json
import torch
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoTokenizer, AutoProcessor
import gc
from typing import List, Tuple
import re
import tempfile


class NanonetsOCRProcessor:
    def __init__(self, output_base_dir: str = "../data/output/ocr_results"):
        """Initialize the OCR processor with Nanonets model"""
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(exist_ok=True)

        print("Loading Nanonets-OCR2-3B model with CPU offloading...")
        print("This may be slow but will work with 8GB GPU")
        model_path = 'nanonets/Nanonets-OCR2-3B'

        # Aggressive CPU offloading - only keep essential layers on GPU
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="balanced",  # Balanced distribution between GPU and CPU
            low_cpu_mem_usage=True,
            offload_folder="offload",  # Use disk for extreme offloading if needed
            offload_state_dict=True,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.processor = AutoProcessor.from_pretrained(model_path)

        self.model.eval()

        # Clear cache
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
        """Perform OCR on a single image with aggressive memory management"""
        with torch.no_grad():
            # Resize to reduce memory
            max_dimension = 1400
            if max(image.size) > max_dimension:
                ratio = max_dimension / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                print(f"  Resized image to {new_size}")

            # Save temporarily
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

                # Generate with reduced batch size and tokens
                output_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    num_beams=1,  # Greedy decoding to save memory
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

            # Aggressive cleanup
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

        # Document header patterns
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

    def process_pdf(self, pdf_path: str, dpi: int = 150) -> None:
        """Process a single PDF file"""
        pdf_path = Path(pdf_path)
        print(f"\n{'='*60}")
        print(f"Processing: {pdf_path.name}")
        print(f"{'='*60}")

        pdf_output_dir = self.output_base_dir / pdf_path.stem
        pdf_output_dir.mkdir(exist_ok=True)

        images = self.pdf_to_images(str(pdf_path), dpi=dpi)

        current_document_pages = []
        document_num = 1
        previous_result = None

        for page_num, image in enumerate(images):
            print(f"\nProcessing page {page_num + 1}/{len(images)}...")

            try:
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

            except Exception as e:
                print(f"  ERROR on page {page_num + 1}: {e}")
                # Save empty result to continue
                current_document_pages.append((page_num, f"[ERROR: {e}]"))

            del image
            gc.collect()

        # Save last document
        if current_document_pages:
            self.save_document(
                pdf_output_dir,
                current_document_pages,
                document_num,
                pdf_path.stem
            )

        self.save_summary(pdf_output_dir, pdf_path.stem, document_num, len(images))

        print(f"\nCompleted! Found {document_num} document(s) in {len(images)} pages")
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
                    num_docs: int, num_pages: int) -> None:
        """Save processing summary"""
        summary = {
            "pdf_name": pdf_name,
            "total_pages": num_pages,
            "documents_found": num_docs,
            "output_directory": str(output_dir)
        }

        with open(output_dir / "_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)

    def process_directory(self, input_dir: str) -> None:
        """Process all PDFs in a directory"""
        input_path = Path(input_dir)
        pdf_files = sorted(input_path.glob("*.pdf"))

        print(f"Found {len(pdf_files)} PDF files to process")

        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}]")
            try:
                self.process_pdf(str(pdf_file))
            except Exception as e:
                print(f"ERROR processing {pdf_file.name}: {e}")
                continue

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()

        print(f"\n{'='*60}")
        print(f"All complete! Processed {len(pdf_files)} PDFs")
        print(f"Output directory: {self.output_base_dir}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Nanonets OCR with CPU offloading")
    parser.add_argument("--input-dir", default="../data/input")
    parser.add_argument("--output-dir", default="../data/output/ocr_results")
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--single-pdf", type=str, default=None)

    args = parser.parse_args()

    # Create offload directory
    Path("offload").mkdir(exist_ok=True)

    processor = NanonetsOCRProcessor(output_base_dir=args.output_dir)

    if args.single_pdf:
        processor.process_pdf(args.single_pdf, dpi=args.dpi)
    else:
        processor.process_directory(args.input_dir)


if __name__ == "__main__":
    main()
