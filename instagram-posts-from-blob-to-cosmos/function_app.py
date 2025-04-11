import logging
import json
import os
from datetime import datetime
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient, PartitionKey

app = func.FunctionApp()

def extract_data(json_data):
    """Extract relevant fields from JSON data"""
    try:
        extracted = {
            "owner": {
                "username": json_data.get("owner", {}).get("username"),
                "is_unpublished": json_data.get("owner", {}).get("is_unpublished"),
                "full_name": json_data.get("owner", {}).get("full_name"),
                "is_verified": json_data.get("owner", {}).get("is_verified"),
                "id": json_data.get("owner", {}).get("id"),
                "is_private": json_data.get("owner", {}).get("is_private")
            },
            "location": json_data.get("location"),
            "shortcode": json_data.get("shortcode"),
            "is_ad": json_data.get("is_ad"),
            "taken_at_timestamp": json_data.get("taken_at_timestamp"),
            "comments_disabled": json_data.get("comments_disabled")
        }
        
        caption_edges = json_data.get("edge_media_to_caption", {}).get("edges", [])
        if caption_edges and "node" in caption_edges[0] and "text" in caption_edges[0]["node"]:
            extracted["caption"] = caption_edges[0]["node"]["text"]
        else:
            extracted["caption"] = None
            
        comment_data = json_data.get("edge_media_preview_comment", {})
        extracted["comments_count"] = comment_data.get("count", 0)
        extracted["comments_preview"] = []
        
        for comment in comment_data.get("edges", []):
            if "node" in comment:
                node = comment["node"]
                extracted["comments_preview"].append({
                    "text": node.get("text"),
                    "created_at": node.get("created_at"),
                    "owner": {
                        "username": node.get("owner", {}).get("username"),
                        "is_verified": node.get("owner", {}).get("is_verified"),
                        "id": node.get("owner", {}).get("id")
                    }
                })
        
        extracted["id"] = json_data.get("shortcode") or json_data.get("id")
        
        return extracted
    except Exception as e:
        logging.error(f"Error extracting data: {str(e)}")
        raise

@app.timer_trigger(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=True, use_monitor=False) 
def posts_from_blob_to_cosmos(myTimer: func.TimerRequest) -> None:
    logging.info('Starting blob processing function')
    
    connection_string = os.environ["AzureWebJobsStorage"]
    source_container_name = os.environ.get("SOURCE_CONTAINER", "posts")
    target_container_name = os.environ.get("TARGET_CONTAINER", "synced")
    cosmos_endpoint = os.environ["COSMOS_ENDPOINT"]
    cosmos_key = os.environ["COSMOS_KEY"]
    cosmos_db_name = os.environ.get("COSMOS_DB_NAME", "instagram")
    cosmos_container_name = os.environ.get("COSMOS_CONTAINER_NAME", "posts")
    max_blobs_per_execution = int(os.environ.get("MAX_BLOBS_PER_EXECUTION", "100"))
    
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        source_container_client = blob_service_client.get_container_client(source_container_name)
        target_container_client = blob_service_client.get_container_client(target_container_name)
        
        cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
        database = cosmos_client.get_database_client(cosmos_db_name)
        container = database.get_container_client(cosmos_container_name)
        
        blobs = []
        count = 0
        for blob in source_container_client.list_blobs():
            if count >= max_blobs_per_execution:
                break
            blobs.append(blob)
            count += 1
        
        processed_count = 0
        error_count = 0
        
        for blob in blobs:
            try:
                blob_name = blob.name
                logging.info(f"Processing blob: {blob_name}")
                
                blob_client = source_container_client.get_blob_client(blob_name)
                blob_data = blob_client.download_blob().readall()
                
                json_data = json.loads(blob_data)
                
                extracted_data = extract_data(json_data)
                
                container.upsert_item(extracted_data)
                
                target_blob_client = target_container_client.get_blob_client(blob_name)
                target_blob_client.upload_blob(blob_data, overwrite=True)
                
                blob_client.delete_blob()
                
                processed_count += 1
                logging.info(f"Successfully processed blob: {blob_name}")
                
            except Exception as e:
                error_count += 1
                logging.error(f"Error processing blob {blob.name}: {str(e)}")
        
        logging.info(f"Function execution completed. Processed: {processed_count}, Errors: {error_count}")
        
    except Exception as e:
        logging.error(f"Error in function execution: {str(e)}")
