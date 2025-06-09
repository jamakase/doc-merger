import os
import requests
import zipfile
import tarfile
import rarfile
import shutil
from pathlib import Path
from PyPDF2 import PdfMerger, PdfReader
import pytesseract
from pdf2image import convert_from_path
import docx2txt
import subprocess
from typing import List, Literal
import logging
from PIL import Image
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_file(url: str, save_path: str) -> None:
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def extract_archive(archive_path: str, extract_to: str) -> None:
    try:
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        elif archive_path.endswith(('.tar', '.tar.gz', '.tgz')):
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_to)
        elif archive_path.endswith('.rar'):
            with rarfile.RarFile(archive_path, 'r') as rar_ref:
                rar_ref.extractall(extract_to)
        logger.info(f"Successfully extracted: {archive_path}")
    except Exception as e:
        logger.error(f"Failed to extract archive {archive_path}: {str(e)}")

def process_archives_recursive(directory: str) -> None:
    """Recursively process all archives in directory and subdirectories"""
    processed_archives: set[str] = set()
    
    def process_directory(dir_path: str) -> None:
        # Get list of files first to avoid modification during iteration
        files_to_process: List[str] = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith(('.zip', '.tar', '.tar.gz', '.tgz', '.rar')):
                    files_to_process.append(file_path)
        
        for file_path in files_to_process:
            # Skip if already processed
            if file_path in processed_archives:
                continue
                
            # Skip macOS system files
            if is_macos_system_file(file_path):
                continue
            
            # Skip if file no longer exists (might have been deleted)
            if not os.path.exists(file_path):
                continue
                
            root = os.path.dirname(file_path)
            file = os.path.basename(file_path)
            extract_dir = os.path.join(root, f"{os.path.splitext(file)[0]}_extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            logger.info(f"Processing archive: {file_path}")
            extract_archive(file_path, extract_dir)
            processed_archives.add(file_path)
            
            # Remove the processed archive to avoid duplication
            try:
                os.remove(file_path)
                logger.info(f"Removed processed archive: {file_path}")
            except Exception as e:
                logger.warning(f"Could not remove archive {file_path}: {str(e)}")
            
            # Recursively process the extracted directory
            process_directory(extract_dir)
    
    process_directory(directory)

def convert_image_to_pdf(image_path: str, output_dir: str) -> str:
    """Convert image to PDF"""
    try:
        output_path = os.path.join(output_dir, f"{Path(image_path).stem}.pdf")
        
        # Open and convert image to PDF
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as PDF
            img.save(output_path, "PDF", resolution=100.0)
        
        logger.info(f"Successfully converted image to PDF: {image_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to convert image {image_path} to PDF: {str(e)}")
        raise

def convert_to_pdf(file_path: str, output_dir: str) -> str:
    """Convert any supported file to PDF"""
    file_ext = Path(file_path).suffix.lower()
    output_path = os.path.join(output_dir, f"{Path(file_path).stem}.pdf")
    
    try:
        if file_ext == '.pdf':
            return file_path
        elif file_ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}:
            return convert_image_to_pdf(file_path, output_dir)
        elif file_ext in {'.doc', '.docx'}:
            # Convert DOC/DOCX to PDF using LibreOffice
            result = subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', output_dir, file_path], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"LibreOffice conversion failed: {result.stderr}")
            return output_path
        elif file_ext in {'.txt', '.rtf', '.odt'}:
            # Convert text files to PDF using LibreOffice
            result = subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', output_dir, file_path],
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"LibreOffice conversion failed: {result.stderr}")
            return output_path
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    except Exception as e:
        logger.error(f"Failed to convert file {file_path} to PDF: {str(e)}")
        raise

def convert_to_text(file_path: str, output_dir: str) -> str:
    """Convert any supported file to text"""
    file_ext = Path(file_path).suffix.lower()
    output_path = os.path.join(output_dir, f"{Path(file_path).stem}.txt")
    
    try:
        if file_ext == '.txt':
            return file_path
        elif file_ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}:
            # Use OCR to extract text from images
            text = pytesseract.image_to_string(Image.open(file_path), lang='eng+rus')
            # Ensure text is a string
            if isinstance(text, bytes):
                text = text.decode('utf-8')
            elif not isinstance(text, str):
                text = str(text)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return output_path
        elif file_ext in {'.doc', '.docx'}:
            # Extract text from DOC/DOCX
            text = docx2txt.process(file_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return output_path
        elif file_ext == '.pdf':
            # Convert PDF to text using OCR
            images = convert_from_path(file_path)
            text = ""
            for image in images:
                ocr_result = pytesseract.image_to_string(image, lang='eng+rus')
                # Ensure text is a string
                if isinstance(ocr_result, bytes):
                    ocr_result = ocr_result.decode('utf-8')
                elif not isinstance(ocr_result, str):
                    ocr_result = str(ocr_result)
                text += ocr_result
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return output_path
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    except Exception as e:
        logger.error(f"Failed to convert file {file_path} to text: {str(e)}")
        raise

def is_macos_system_file(file_path: str) -> bool:
    """Check if file is a macOS system file that should be ignored"""
    filename = os.path.basename(file_path)
    path_parts = Path(file_path).parts
    
    # Skip files in __MACOSX directory
    if '__MACOSX' in path_parts:
        return True
    
    # Skip dot files created by macOS (resource forks)
    if filename.startswith('._'):
        return True
    
    # Skip .DS_Store files
    if filename == '.DS_Store':
        return True
    
    # Skip very small files (likely corrupted or system files)
    try:
        if os.path.getsize(file_path) < 100:  # Less than 100 bytes
            return True
    except (OSError, IOError):
        return True
    
    return False

def organize_documents(directory: str, output_dir: str, mode: Literal['pdf', 'txt'] = 'pdf') -> None:
    # Include image extensions
    doc_extensions = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
    all_extensions = doc_extensions | image_extensions
    
    converted_files: List[str] = []
    processed_files = 0
    failed_files = 0
    
    logger.info(f"Starting document organization in mode: {mode}")
    
    for root, _, files in os.walk(directory):
        for file in files:
            src_path = os.path.join(root, file)
            
            # Skip macOS system files
            if is_macos_system_file(src_path):
                logger.debug(f"Skipping macOS system file: {src_path}")
                continue
                
            if Path(file).suffix.lower() in all_extensions:
                logger.info(f"Processing file: {src_path}")
                processed_files += 1
                
                try:
                    if mode == 'pdf':
                        converted_path = convert_to_pdf(src_path, output_dir)
                    else:
                        converted_path = convert_to_text(src_path, output_dir)
                    
                    if converted_path and os.path.exists(converted_path):
                        converted_files.append(converted_path)
                        logger.info(f"Successfully processed: {file}")
                    else:
                        logger.error(f"Conversion failed - output file not found: {file}")
                        failed_files += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process file {file}: {str(e)}")
                    failed_files += 1
    
    logger.info(f"Processing complete. Processed: {processed_files}, Failed: {failed_files}, Successfully converted: {len(converted_files)}")
    
    # Create final combined file
    if converted_files:
        if mode == 'pdf':
            merger = PdfMerger()
            merged_count = 0
            
            for pdf in converted_files:
                try:
                    # Verify PDF is valid before merging
                    with open(pdf, 'rb') as f:
                        reader = PdfReader(f)
                        if len(reader.pages) > 0:
                            merger.append(pdf)
                            merged_count += 1
                            logger.info(f"Successfully merged: {os.path.basename(pdf)}")
                        else:
                            logger.error(f"Empty PDF file, skipping: {os.path.basename(pdf)}")
                except Exception as e:
                    logger.error(f"Could not merge {os.path.basename(pdf)}: {str(e)}")
                    
            try:
                final_pdf_path = os.path.join(output_dir, 'final.pdf')
                merger.write(final_pdf_path)
                logger.info(f"Final PDF created successfully with {merged_count} files: {final_pdf_path}")
            except Exception as e:
                logger.error(f"Could not write final.pdf: {str(e)}")
            finally:
                merger.close()
        else:
            # Combine all text files
            final_txt_path = os.path.join(output_dir, 'final.txt')
            combined_count = 0
            
            with open(final_txt_path, 'w', encoding='utf-8') as outfile:
                for txt_file in converted_files:
                    try:
                        with open(txt_file, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            if content.strip():  # Only add non-empty files
                                outfile.write(f"\n--- {os.path.basename(txt_file)} ---\n")
                                outfile.write(content + '\n\n')
                                combined_count += 1
                    except Exception as e:
                        logger.error(f"Could not read {os.path.basename(txt_file)}: {str(e)}")
            
            logger.info(f"Final text file created successfully with {combined_count} files: {final_txt_path}")
    else:
        logger.warning("No files were successfully converted!")

def main(url: str, mode: Literal['pdf', 'txt'] = 'pdf') -> None:
    logger.info(f"Starting extraction process in {mode} mode")
    
    # Create temporary directory for downloads
    temp_dir = "temp_downloads"
    extract_dir = os.path.join(temp_dir, "extracted")
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(extract_dir, exist_ok=True)
    
    try:
        # Download the file
        zip_path = os.path.join(temp_dir, "downloaded.zip")
        logger.info(f"Downloading file from: {url}")
        download_file(url, zip_path)
        logger.info("Download completed")
        
        # Extract initial archive to separate directory
        logger.info("Extracting initial archive")
        extract_archive(zip_path, extract_dir)
        
        # Remove the downloaded archive to avoid duplication
        os.remove(zip_path)
        logger.info("Removed original downloaded archive")
        
        # Process any nested archives recursively
        logger.info("Processing nested archives recursively")
        process_archives_recursive(extract_dir)
        
        # Create output directory for documents
        output_dir = "extracted_documents"
        os.makedirs(output_dir, exist_ok=True)
        
        # Organize documents (now only from extract_dir)
        logger.info("Organizing and converting documents")
        organize_documents(extract_dir, output_dir, mode)
        
        logger.info("Process completed successfully")
        
    except Exception as e:
        logger.error(f"Main process failed: {str(e)}")
        raise
    finally:
        # Cleanup
        logger.info("Cleaning up temporary files")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    url = "https://abitlk.itmo.ru/api/v1/36b2be2f442ca8fc0b3b021f313a46f4031b88c5f0ada624091d687366fd737f/storage/show_file?file=/file_storage/users/71876/117966/master/portfolio_archive_all_files/2025/06/1749138270_47082200.zip"
    main(url, mode='pdf')  # or mode='txt' for text output
