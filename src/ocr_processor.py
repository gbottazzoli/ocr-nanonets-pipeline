#!/usr/bin/env python3
"""
OCR processor for historical PDF documents using Nanonets-OCR2-3B
Optimized for 8GB GPU memory
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


class NanonetsOCRProcessor:
    def __init__(self, output_base_dir: str = "../data/output/ocr_results", device: str = None):
        """Initialize the OCR processor with Nanonets model"""
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(exist_ok=True)

        # Auto-detect device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"Using device: {self.device}")

        # Load model with memory optimization for 8GB GPU
        print("Loading Nanonets-OCR2-3B model (FP16 optimized)...")
        model_path = 'nanonets/Nanonets-OCR2-3B'

        # Use FP16 and aggressive memory management
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else self.device,
            low_cpu_mem_usage=True,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.processor = AutoProcessor.from_pretrained(model_path)

        self.model.eval()  # Set to evaluation mode

        # Enable memory efficient inference
        if self.device == "cuda":
            torch.cuda.empty_cache()

        print("Model loaded successfully!")

    def pdf_to_images(self, pdf_path: str, dpi: int = 150) -> List[Image.Image]:
        """Convert PDF to images with memory efficiency"""
        print(f"Converting PDF to images: {pdf_path}")

        # Convert PDF to images
        # Using lower DPI to save memory, can increase if needed
        images = convert_from_path(pdf_path, dpi=dpi)
        print(f"Converted {len(images)} pages")

        return images

    def ocr_image(self, image: Image.Image, max_new_tokens: int = 2048) -> str:
        """Perform OCR on a single image"""
        with torch.no_grad():
            # Resize large images to save memory
            max_dimension = 1600  # Reduce if still running out of memory
            if max(image.size) > max_dimension:
                ratio = max_dimension / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Save image temporarily for processing
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                image.save(tmp_path)

            try:
                # Prepare the prompt and messages
                prompt = """Extract the text from the above document as if you were reading it naturally. Return the tables in html format if present. Return the equations in LaTeX representation if present."""

                messages = [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": [
                        {"type": "image", "image": f"file://{tmp_path}"},
                        {"type": "text", "text": prompt},
                    ]},
                ]

                # Apply chat template
                text = self.processor.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )

                # Process inputs
                inputs = self.processor(
                    text=[text],
                    images=[image],
                    padding=True,
                    return_tensors="pt"
                )
                inputs = inputs.to(self.model.device)

                # Generate OCR output
                output_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False
                )

                # Decode output
                generated_ids = [
                    output_ids[len(input_ids):]
                    for input_ids, output_ids in zip(inputs.input_ids, output_ids)
                ]

                output_text = self.processor.batch_decode(
                    generated_ids,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=True
                )

                result = output_text[0]

            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            # Clear GPU cache after each image
            if self.device == "cuda":
                torch.cuda.empty_cache()

            return result

    def detect_document_boundary(self, current_result: str, previous_result: str = None) -> bool:
        """
        Detect if current page starts a new document based on visual layout changes

        Heuristics:
        - Large title/header at top of page
        - Significant change in font size distribution
        - Page starts with common document headers (e.g., dates, reference numbers)
        """
        if previous_result is None:
            return True  # First page is always a new document

        # Extract text from current page
        current_text = self.extract_text_from_result(current_result)

        # Check for new document indicators
        # 1. Check if page starts with a title-like pattern (short first line, larger gap)
        lines = current_text.strip().split('\n')
        if not lines:
            return False

        first_line = lines[0].strip()

        # 2. Check for document header patterns (dates, reference numbers, etc.)
        header_patterns = [
            r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # Dates
            r'^[A-Z]\d{4}[-\s]',  # Reference numbers like R1048-
            r'^(DOCUMENT|LETTER|MEMO|REPORT)',  # Common document types
            r'^\d+\s+(January|February|March|April|May|June|July|August|September|October|November|December)',
        ]

        for pattern in header_patterns:
            if re.search(pattern, first_line, re.IGNORECASE):
                return True

        # 3. Check if first line is short and potentially a title (< 60 chars, > 5 chars)
        if 5 < len(first_line) < 60 and len(lines) > 2:
            # Check if followed by blank line or significant content
            return True

        return False

    def extract_text_from_result(self, result: str) -> str:
        """Extract plain text from OCR result"""
        # Result is already plain text from the model
        return result

    def format_as_markdown(self, pages_data: List[Tuple[int, str]], document_num: int) -> str:
        """Format OCR results as markdown"""
        md_content = f"# Document {document_num}\n\n"
        md_content += f"Pages: {pages_data[0][0] + 1}"
        if len(pages_data) > 1:
            md_content += f" - {pages_data[-1][0] + 1}"
        md_content += f" ({len(pages_data)} page{'s' if len(pages_data) > 1 else ''})\n\n"
        md_content += "---\n\n"

        for page_num, result in pages_data:
            text = self.extract_text_from_result(result)
            md_content += f"## Page {page_num + 1}\n\n"
            md_content += text + "\n\n"
            md_content += "---\n\n"

        return md_content

    def process_pdf(self, pdf_path: str) -> None:
        """Process a single PDF file"""
        pdf_path = Path(pdf_path)
        print(f"\n{'='*60}")
        print(f"Processing: {pdf_path.name}")
        print(f"{'='*60}")

        # Create output folder for this PDF
        pdf_output_dir = self.output_base_dir / pdf_path.stem
        pdf_output_dir.mkdir(exist_ok=True)

        # Convert PDF to images
        images = self.pdf_to_images(str(pdf_path))

        # Process pages and detect document boundaries
        all_results = []
        current_document_pages = []
        document_num = 1
        previous_result = None

        for page_num, image in enumerate(images):
            print(f"Processing page {page_num + 1}/{len(images)}...")

            # Perform OCR
            result = self.ocr_image(image)
            all_results.append((page_num, result))

            # Check if this page starts a new document
            is_new_doc = self.detect_document_boundary(result, previous_result)

            if is_new_doc and current_document_pages:
                # Save previous document
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

            # Clear memory
            del image
            gc.collect()

        # Save the last document
        if current_document_pages:
            self.save_document(
                pdf_output_dir,
                current_document_pages,
                document_num,
                pdf_path.stem
            )

        # Save summary
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

        summary_file = output_dir / "_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

    def process_directory(self, input_dir: str, pattern: str = "*.pdf") -> None:
        """Process all PDFs in a directory"""
        input_path = Path(input_dir)
        pdf_files = sorted(input_path.glob(pattern))

        print(f"Found {len(pdf_files)} PDF files to process")

        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}]")
            try:
                self.process_pdf(str(pdf_file))
            except Exception as e:
                print(f"ERROR processing {pdf_file.name}: {e}")
                continue

            # Clear GPU memory between PDFs
            if self.device == "cuda":
                torch.cuda.empty_cache()
                gc.collect()

        print(f"\n{'='*60}")
        print(f"All processing complete! Processed {len(pdf_files)} PDFs")
        print(f"Output directory: {self.output_base_dir}")
        print(f"{'='*60}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="OCR processor for historical PDFs")
    parser.add_argument("--input-dir", default="../data/input",
                       help="Input directory containing PDFs")
    parser.add_argument("--output-dir", default="../data/output/ocr_results",
                       help="Output directory for OCR results")
    parser.add_argument("--dpi", type=int, default=150,
                       help="DPI for PDF to image conversion (default: 150, lower = less memory)")
    parser.add_argument("--single-pdf", type=str, default=None,
                       help="Process a single PDF file instead of directory")

    args = parser.parse_args()

    # Initialize processor
    processor = NanonetsOCRProcessor(output_base_dir=args.output_dir)

    # Process PDFs
    if args.single_pdf:
        processor.process_pdf(args.single_pdf)
    else:
        processor.process_directory(args.input_dir)


if __name__ == "__main__":
    main()
