import json
import logging
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import tenacity
from azure.storage.blob import BlobServiceClient
from tqdm import tqdm

# AZURE BLOB STORAGE CONNECTION DETAILS
STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"
CONTAINER_NAME = "posts"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='upload_log.txt'
)
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
logging.getLogger('').addHandler(console)

logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)


def create_blob_service_client():
    """Create a properly configured blob service client with minimal configuration to ensure compatibility"""
    return BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(),
    wait=tenacity.wait_exponential(multiplier=1, min=1, max=60),
    stop=tenacity.stop_after_attempt(5),
    before_sleep=lambda retry_state: logging.info(
        f"Retrying upload after error: {retry_state.outcome.exception()}. Attempt {retry_state.attempt_number}")
)
def upload_file(blob_client, filename, data):
    """Upload a single file to blob storage with retries"""
    try:
        json_content = json.dumps(data)
        blob_client.upload_blob(json_content, overwrite=True)
        return True
    except Exception as e:
        logging.error(f"Error uploading {filename}: {str(e)}")
        raise


def process_batch(file_batch, container_client):
    """Process a batch of files for upload"""
    results = []
    for filename, data in file_batch:
        try:
            blob_name = f"{os.path.splitext(filename)[0]}_{uuid.uuid4()}.json"
            blob_client = container_client.get_blob_client(blob_name)
            success = upload_file(blob_client, filename, data)
            results.append((filename, True))
        except Exception as e:
            logging.error(f"Error processing {filename}: {str(e)}")
            results.append((filename, False))
    return results


def read_info_files(directory_path, max_files=None):
    """Read all .info files with progress bar"""
    info_data = []

    all_files = [f for f in os.listdir(directory_path) if f.endswith('.info')]

    if max_files:
        all_files = all_files[:max_files]

    total_files = len(all_files)

    logging.info(f"Found {total_files} .info files to process")

    for filename in tqdm(all_files, desc="Reading files"):
        file_path = os.path.join(directory_path, filename)
        try:
            with open(file_path, 'r') as file:
                json_data = json.load(file)
                info_data.append((filename, json_data))
        except json.JSONDecodeError:
            logging.warning(f"Error: {filename} contains invalid JSON")
        except Exception as e:
            logging.warning(f"Error reading {filename}: {str(e)}")

    return info_data


def upload_to_blob_storage(file_data_list, batch_size=50, max_workers=8):
    """Upload files to Azure Blob Storage in parallel batches with connection pool management"""
    start_time = time.time()

    blob_service_client = create_blob_service_client()

    try:
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        try:
            container_client.get_container_properties()
            logging.info(f"Container '{CONTAINER_NAME}' exists")
        except Exception:
            container_client.create_container()
            logging.info(f"Container '{CONTAINER_NAME}' created")
    except Exception as e:
        logging.error(f"Error with container: {str(e)}")
        return 0, 0, 0

    total_files = len(file_data_list)
    batches = [file_data_list[i:i + batch_size] for i in range(0, total_files, batch_size)]

    successful_uploads = 0
    failed_uploads = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for batch in batches:
            batch_container_client = blob_service_client.get_container_client(CONTAINER_NAME)
            futures.append(executor.submit(process_batch, batch, batch_container_client))

        for future in tqdm(futures, desc="Uploading batches"):
            results = future.result()
            for filename, success in results:
                if success:
                    successful_uploads += 1
                else:
                    failed_uploads += 1

    elapsed_time = time.time() - start_time

    logging.info(f"Upload complete in {elapsed_time:.2f} seconds")
    logging.info(f"Successful uploads: {successful_uploads}")
    logging.info(f"Failed uploads: {failed_uploads}")
    if elapsed_time > 0:
        logging.info(f"Average upload rate: {successful_uploads / elapsed_time:.2f} files/second")
    else:
        logging.info("Average upload rate: N/A (no time elapsed)")

    return successful_uploads, failed_uploads, elapsed_time


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Upload JSON data from .info files to Azure Blob Storage")
    parser.add_argument("--directory", type=str, required=True, help="Directory containing .info files")
    parser.add_argument("--batch-size", type=int, default=50, help="Number of files per batch")
    parser.add_argument("--max-workers", type=int, default=8, help="Maximum number of parallel workers")
    parser.add_argument("--max-files", type=int, help="Maximum number of files to process (for testing)")

    args = parser.parse_args()

    print(f"Reading .info files from {args.directory}")
    info_data = read_info_files(args.directory, args.max_files)

    if info_data:
        print(f"Uploading {len(info_data)} files to Blob Storage")
        print(f"Using {args.max_workers} workers and batch size of {args.batch_size}")
        successful, failed, elapsed = upload_to_blob_storage(
            info_data,
            batch_size=args.batch_size,
            max_workers=args.max_workers
        )

        print(f"Upload complete in {elapsed:.2f} seconds")
        print(f"Successful uploads: {successful}")
        print(f"Failed uploads: {failed}")
        if elapsed > 0:
            print(f"Average upload rate: {successful / elapsed:.2f} files/second")
        else:
            print("Average upload rate: N/A (no time elapsed)")
    else:
        print("No valid .info files found")
