import motor.motor_asyncio
import asyncio
import json
from config import Config
from pymongo import UpdateOne

# Constants
DB_URL = Config.DB_URL
DB_NAME = "APPX_API"  # As defined in master/key.py
COLLECTION_NAME = "appx_api"

async def upload_apis():
    try:
        print(f"Connecting to MongoDB at {DB_URL}...")
        # Connect to Database
        client = motor.motor_asyncio.AsyncIOMotorClient(DB_URL)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        print(f"Connected to database: {DB_NAME}, collection: {COLLECTION_NAME}")

        # Read JSON file
        print("Reading appxapis.json...")
        try:
            with open('appxapis.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print("Error: appxapis.json file not found.")
            return
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON from appxapis.json.")
            return

        if not isinstance(data, list):
            print("Error: appxapis.json content is not a list.")
            return

        print(f"Found {len(data)} APIs in appxapis.json.")
        
        # Prepare bulk operations
        operations = []
        for item in data:
            name = item.get("name")
            api = item.get("api")
            if name and api:
                # Upsert based on API URL to avoid duplicates
                operations.append(
                    UpdateOne(
                        {"api": api},
                        {"$set": {"name": name, "api": api}},
                        upsert=True
                    )
                )
            else:
                 print(f"Skipping invalid item: {item}")

        if operations:
            print(f"Starting bulk write operation for {len(operations)} items...")
            result = await collection.bulk_write(operations)
            print("-" * 30)
            print(f"Upload complete.")
            print(f"Inserted (New): {result.upserted_count}")
            print(f"Modified (Updated): {result.modified_count}")
            print(f"Matched (Existing): {result.matched_count}")
            print("-" * 30)
            
            # Verify count
            count = await collection.count_documents({})
            print(f"Total documents in collection now: {count}")
            
        else:
            print("No valid data to upload.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(upload_apis())
