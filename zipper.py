
import os
import sys
import shutil
import zipfile
from pathlib import Path
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import io
import base64
import json
import random
import string
import gc  # For memory management

# Constants
CHUNK_SIZE = 16 * 1024 * 1024  # 16MB chunks for performance  # 16MB chunks for better performance
MAX_ARCHIVE_SIZE = 256 * 1024 * 1024  # 256MB per JSON file
MAX_BATCH_FILES = 1000  # Maximum number of files per batch

def add_random_suffix(data):
    """Add some random data to make the encoded content look more random"""
    suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    return data + suffix

def zip_large_file(zip_handle, file_path, arcname):
    """Stream a large file into the zip archive without loading it all into memory"""
    with open(file_path, 'rb') as f:
        with zip_handle.open(arcname, 'w') as dest:
            shutil.copyfileobj(f, dest, CHUNK_SIZE)

def process_files_batch(args):
    """Process a batch of files into encoded JSON using ZIP compression internally"""
    files, folder, output_path, progress_callback = args
    total_size = 0
    json_entries = []
    
    # Pre-allocate memory for the batch
    json_entries = []
    buffer = io.BytesIO()  # Reuse buffer for all files
    
    # Process each file in the batch
    total_files = sum(len(batch) for batch in [files])  # Total files in this batch
    processed_files = 0
    
    for file in files:
        try:
            rel_path = str(file.relative_to(folder))
            
            # Reset buffer position
            buffer.seek(0)
            buffer.truncate()
            
            # Use ZIP compression in memory with reused buffer
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(str(file), rel_path)
            
            # Get compressed data and encode it
            compressed_data = buffer.getvalue()
            encoded = add_random_suffix(base64.b64encode(compressed_data).decode('utf-8'))
            
            # Create JSON entry with minimal overhead
            json_entries.append({'r': rel_path, 'c': encoded})
            total_size += file.stat().st_size
            
            # Update progress
            processed_files += 1
            if progress_callback:
                progress_callback(processed_files, total_files)
            
        except Exception as e:
            print(f"Error processing {file}: {e}")
    
    if json_entries:
        try:
            # Use faster JSON dump
            with open(output_path, 'w', encoding='utf-8') as jf:
                json.dump(json_entries, jf, separators=(',', ':'))  # Use compact JSON format
        except Exception as e:
            print(f"Error saving {output_path}: {e}")
            return None, 0
    
    return output_path, total_size

def zip_folder(folder_path, progress_callback=None):
    """Create encoded JSON archives of a folder using ZIP compression internally"""
    output_dir = None
    if isinstance(folder_path, (list, tuple)):
        folder = Path(folder_path[0])
        output_dir = Path(folder_path[1]) if len(folder_path) > 1 else None
    else:
        folder = Path(folder_path)
    
    if not folder.is_dir():
        print(f"{folder} is not a valid directory.")
        return
    
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = folder
        
    MAX_ARCHIVE_SIZE = 100 * 1024 * 1024  # 100MB per JSON file for better handling
    
    # Collect all files first for accurate progress tracking
    print("Scanning for files...")
    files = list(folder.rglob('*'))
    files = [f for f in files if f.is_file() and not str(f).lower().endswith('.json')]
    if not files:
        print("No files to archive.")
        return
        
    total_files = len(files)
    processed_files = 0
    
    # Report initial progress
    if progress_callback:
        progress_callback(processed_files, total_files)

    # Group files into batches optimized for performance
    batches = []
    current_batch = []
    current_batch_size = 0
    
    for file in sorted(files, key=lambda x: x.stat().st_size):
        file_size = file.stat().st_size
        estimated_size = file_size * 1.4  # Base64 overhead estimate
        
        # Start new batch if current would be too large or has too many files
        if current_batch and (current_batch_size + estimated_size > MAX_ARCHIVE_SIZE or 
                            len(current_batch) >= MAX_BATCH_FILES):
            batches.append(current_batch)
            current_batch = []
            current_batch_size = 0
        
        current_batch.append(file)
        current_batch_size += estimated_size

    if current_batch:
        batches.append(current_batch)

    if not batches:
        print("No files to process after batch calculation.")
        return

    # Process batches in parallel for maximum performance
    print(f"Processing {len(batches)} batch(es) of files...")
    successful_archives = []
    total_files = sum(len(batch) for batch in batches)
    processed_files = 0
    
    # Use optimal number of workers based on CPU cores and batch count
    workers = min(len(batches), mp.cpu_count() * 2)
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for i, batch in enumerate(batches, 1):
            json_path = output_dir / f"archive_{i}.json"
            futures.append(executor.submit(process_files_batch, (batch, folder, json_path, progress_callback)))
        
        # Process results as they complete
        for i, future in enumerate(futures, 1):
            try:
                archive_path, size = future.result(timeout=300)  # 5-minute timeout per batch
                if archive_path:
                    successful_archives.append(archive_path)
            except Exception as e:
                print(f"Error in batch {i}: {e}")

    if successful_archives:
        # Clean up original files if not using separate output directory
        if not (output_dir and output_dir != folder):
            for file in files:
                try:
                    file.unlink()
                except Exception as e:
                    print(f"Error removing {file}: {e}")
            
            # Remove empty directories
            dirs = sorted([d for d in folder.rglob('*') if d.is_dir() and d != folder], 
                        key=lambda x: -len(str(x)))
            for d in dirs:
                try:
                    d.rmdir()
                except OSError:
                    pass  # Directory not empty
            print(f"Created {len(successful_archives)} JSON archives and deleted originals.")
        else:
            print(f"Created {len(successful_archives)} JSON archives in {output_dir} (source files not deleted).")
    else:
        print("No archives were created successfully.")

def extract_json(json_path, destination, start_offset=0, progress_callback=None):
    """Extract files from an encoded JSON archive"""
    import time
    start_time = time.time()
    
    folder = Path(destination)
    extracted_files = 0
    failed_files = 0
    
    print(f"\nStarting extraction of {json_path}")
    
    # Reuse a single buffer for all files
    zip_buffer = io.BytesIO()
    
    try:
        print(f"Processing {json_path}...")
        
        # Load and process entries
        with open(json_path, 'r', encoding='utf-8') as jf:
            entries = json.load(jf)
            total_entries = len(entries)
            
            # Process each entry
            for i, entry in enumerate(entries, 1):
                try:
                    # Get relative path and normalize it
                    rel_path = entry['r'].replace('\\', '/')
                    
                    if i % 5 == 0 or i == total_entries:
                        elapsed = time.time() - start_time
                        rate = i / elapsed if elapsed > 0 else 0
                        print(f"Processing {i}/{total_entries} files ({rate:.1f} files/sec)")
                    
                    # Decode and decompress
                    encoded_content = entry['c']
                    compressed_data = base64.b64decode(encoded_content[:-8].encode('utf-8'))
                    
                    # Reuse buffer for ZIP data
                    zip_buffer.seek(0)
                    zip_buffer.truncate()
                    zip_buffer.write(compressed_data)
                    zip_buffer.seek(0)
                    
                    # Extract file
                    with zipfile.ZipFile(zip_buffer, 'r') as zf:
                        # Get the first file in the archive (should only be one)
                        zip_info = zf.filelist[0]
                        
                        # Create target path
                        target = folder / rel_path
                        target.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Extract with corrected path
                        with zf.open(zip_info) as source, open(target, 'wb') as dest:
                            shutil.copyfileobj(source, dest, length=CHUNK_SIZE)
                        
                        extracted_files += 1
                        if progress_callback:
                            progress_callback(start_offset + extracted_files, total_entries)
                    
                except Exception as e:
                    failed_files += 1
                    print(f"\nError extracting {rel_path}: {str(e)}")
                    continue
                
                # Free up memory periodically
                if i % 25 == 0:
                    gc.collect()
                
                # Free up memory periodically
                if extracted_files % 10 == 0:
                    gc.collect()
        
        # Report final status
        elapsed = time.time() - start_time
        print(f"\nExtraction completed in {elapsed:.1f}s:")
        print(f"- Successfully extracted: {extracted_files} files")
        if failed_files:
            print(f"- Failed to extract: {failed_files} files")
        
        return failed_files == 0
        
    except Exception as e:
        print(f"Critical error processing {json_path}: {e}")
        import traceback
        print(f"Detailed error:\n{traceback.format_exc()}")
        return False

def unzip_folder(folder_path, progress_callback=None):
    """Extract JSON archives sequentially"""
    import time
    overall_start = time.time()
    
    folder = Path(folder_path)
    print(f"\nScanning {folder} for JSON archives...")
    json_files = sorted(folder.glob('*.json'), 
                       key=lambda x: int(x.stem.split('_')[1]) if x.stem.split('_')[1].isdigit() else 0)
    
    if not json_files:
        print("No JSON archives found to extract.")
        return
        
    # Count total files from all archives for accurate progress tracking
    total_files = 0
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as jf:
                entries = json.load(jf)
                total_files += len(entries)
        except Exception as e:
            print(f"Error reading {json_file}: {e}")
    
    # Report initial progress
    if progress_callback:
        progress_callback(0, total_files)
    
    # Calculate total size for logging
    total_size = sum(f.stat().st_size for f in json_files)
    print(f"\nFound {len(json_files)} JSON archives to extract"
          f" (Total size: {total_size / (1024*1024):.1f} MB)")
    for f in json_files:
        print(f"- {f.name}: {f.stat().st_size / (1024*1024):.1f} MB")
    
    print("\nProcessing archives sequentially to ensure stability...")
    
    successful_files = []
    failed_files = []
    current_offset = 0
    
    # Process one file at a time with progress tracking
    for file_num, json_file in enumerate(json_files, 1):
        print(f"\nProcessing archive {file_num}/{len(json_files)}: {json_file.name}")
        extraction_start = time.time()
        
        try:
            # Get number of files in current archive for progress offset
            with open(json_file, 'r', encoding='utf-8') as jf:
                entries = json.load(jf)
                archive_file_count = len(entries)
            
            # Process the file with progress callback
            if extract_json(json_file, folder, current_offset, progress_callback):
                successful_files.append(json_file)
                current_offset += archive_file_count
                print(f"Successfully completed {json_file.name} in"
                      f" {time.time() - extraction_start:.1f}s")
            else:
                failed_files.append(json_file)
                print(f"Failed to extract {json_file.name}")
            
            # Force memory cleanup after each file
            gc.collect()
            
        except Exception as e:
            print(f"Fatal error extracting {json_file.name}:")
            import traceback
            print(traceback.format_exc())
            failed_files.append(json_file)
        
        # Report results periodically
        if successful_files and (len(successful_files) % 5 == 0 or file_num == len(json_files)):
            total_time = time.time() - overall_start
            print(f"\nSuccessfully extracted {len(successful_files)}/{len(json_files)} archives"
                  f" in {total_time:.1f}s")
            
            # Only remove successfully processed archives
            for completed_file in successful_files[-5:]:  # Only process last batch
                try:
                    completed_file.unlink()
                except Exception as e:
                    print(f"Warning: Could not remove {completed_file.name}: {e}")
    
    if failed_files:
        print(f"\nWarning: Failed to extract {len(failed_files)} archives:")
        for failed in failed_files:
            print(f"- {failed.name}")
        print("\nJSON files for failed extractions were not removed")

def main():
    if len(sys.argv) < 3:
        print("Usage: python zipper.py <zip|unzip> <folder_path> [output_dir_for_zip]")
        return
    operation = sys.argv[1].lower()
    folder_path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None
    if operation == 'zip':
        if output_dir:
            zip_folder([folder_path, output_dir])
        else:
            zip_folder(folder_path)
    elif operation == 'unzip':
        unzip_folder(folder_path)
    else:
        print("Invalid operation. Use 'zip' or 'unzip'.")

if __name__ == "__main__":
    main()
