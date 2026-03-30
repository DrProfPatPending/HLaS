# Language: Python

# Necessary imports
import os
import argparse
from PyPDF2 import PdfReader, PdfWriter


# Function to extract Membership No and Name from text
import re

def extract_membership_and_name(text):
    """
    Extracts the Membership No and Name from the given text.
    Returns (membership_no, name) or (None, None) if not found.
    """
    membership_no = None
    name = None
    # Try to find 'Membership No:' or 'Memship Number:'
    mem_no_match = re.search(r"Membership\s*No\s*:\s*([\w-]+)", text, re.IGNORECASE)
    if not mem_no_match:
        mem_no_match = re.search(r"Memship\s*Number\s*:\s*([\w-]+)", text, re.IGNORECASE)
    if mem_no_match:
        membership_no = mem_no_match.group(1).strip()

    name_match = re.search(r"Name\s*:\s*(.+)", text, re.IGNORECASE)
    if name_match:
        # Take only up to the first newline or up to the next field
        name_line = name_match.group(1).strip()
        name = name_line.split('\n')[0].split('Membership No')[0].strip()

    return membership_no, name

# Function to split PDF and name files by extracted fields
def split_pdf_by_member(input_pdf_path, output_folder, start_page=1, num_pages=None):
    """
    Splits a PDF file into individual pages, extracts Membership No and Name, and saves each page as '<Membership No> - <Name> - 2026.pdf'.
    Allows specifying start_page (1-based) and num_pages to extract a subset.
    """
    os.makedirs(output_folder, exist_ok=True)
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)

    # Calculate page indices
    start_idx = max(0, start_page - 1)
    end_idx = start_idx + num_pages if num_pages is not None else total_pages
    end_idx = min(end_idx, total_pages)

    for i in range(start_idx, end_idx):
        page = reader.pages[i]
        writer = PdfWriter()
        writer.add_page(page)

        # Extract text from the page
        try:
            text = page.extract_text() or ""
        except Exception as e:
            print(f"Warning: Could not extract text from page {i+1}: {e}")
            text = ""

        membership_no, name = extract_membership_and_name(text)
        if membership_no and name:
            # Remove forbidden filename characters and strip whitespace/newlines
            safe_name = re.sub(r'[\\/:*?"<>|\n\r]', '', name).strip()
            safe_no = re.sub(r'[\\/:*?"<>|\n\r]', '', membership_no).strip()
            filename = f"{safe_no} - {safe_name} - 2026.pdf"
        else:
            filename = f"page_{i+1}_unknown.pdf"

        output_file_path = os.path.join(output_folder, filename)
        with open(output_file_path, 'wb') as output_pdf:
            writer.write(output_pdf)

        print(f"Saved page {i+1}/{total_pages} to {output_file_path}")

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split PDF into member cards and name by Membership No and Name.")
    parser.add_argument('--input', type=str, default="GAAFFS_ID_Cards_2026.pdf", help="Input PDF file")
    parser.add_argument('--output', type=str, default="output_pages", help="Output folder for individual pages")
    parser.add_argument('--start', type=int, default=1, help="Start page (1-based index)")
    parser.add_argument('--pages', type=int, default=None, help="Number of pages to extract")
    args = parser.parse_args()

    split_pdf_by_member(
        input_pdf_path=args.input,
        output_folder=args.output,
        start_page=args.start,
        num_pages=args.pages
    )