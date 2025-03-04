from fastapi import FastAPI
import redis
import asyncio
from uvicorn import run
from pydantic import BaseModel

# Configuration
MAX_CLIENTS_PER_ITEM = 2000  # Each item serves 2000 clients before rotating

# Connect to Redis
redis_client = redis.StrictRedis(host="localhost", port=6379, decode_responses=True)

# Initialize FastAPI app
app = FastAPI()

# Initialize Redis data with items from links.txt
def initialize_items(force_reset=False):
    """
    Initialize the Redis database with items from links.txt.

    :param force_reset: If True, clears existing data in Redis before initialization.
    """
    if force_reset:
        redis_client.delete("items")
        redis_client.delete("item_usage")
        print("Redis data cleared.")

    if not redis_client.exists("items"):
        try:
            with open('links.txt', 'r') as file:
                items = [line.strip() for line in file if line.strip()]
            if not items:
                raise ValueError("No items found in links.txt")
            
            redis_client.rpush("items", *items)
            for item in items:
                redis_client.hset("item_usage", item, 0)
            
            print(f"Loaded {len(items)} items into Redis.")
        except FileNotFoundError:
            print("Error: links.txt file not found. Please create the file and add items.")
        except ValueError as e:
            print(f"Error: {e}")

def reset_item_usage():
    """
    Resets the usage count for all items and reloads them into Redis.
    """
    print("Resetting item usage counts and reloading items...")
    redis_client.delete("items")
    
    try:
        with open('links.txt', 'r') as file:
            items = [line.strip() for line in file if line.strip()]
        
        redis_client.rpush("items", *items)
        for item in items:
            redis_client.hset("item_usage", item, 0)
        print("Items and usage counts have been reset.")
    except FileNotFoundError:
        print("Error: links.txt file not found during reset.")

# Endpoint to get an item
@app.get("/get_item")
async def get_item():
    """
    Assigns an item to the client, ensuring no item is overused.
    When all items reach their usage limit, the server resets and starts over.
    """
    async with asyncio.Lock():
        while True:
            item = redis_client.lindex("items", 0)  # Peek at the first item
            if item:
                usage = int(redis_client.hget("item_usage", item) or 0)
                if usage < MAX_CLIENTS_PER_ITEM:
                    redis_client.hincrby("item_usage", item, 1)
                    return {"assigned_item": item, "current_usage": usage + 1}
                else:
                    redis_client.lpop("items")  # Remove item if usage limit is reached
            else:
                # All items exhausted, reset usage and restart
                reset_item_usage()

# Initialize items with a forced reset
initialize_items(force_reset=True)

# Run the server
if __name__ == "__main__":
    run("server:app", host="0.0.0.0", port=8080, log_level="info", reload=True)
