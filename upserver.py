import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI()

# Define request model
class LinkData(BaseModel):
    link: str

# Function to save links to a file
def save_link(link: str):
    with open("download_links.txt", "a") as f:
        f.write(link + "\n")

# Define FastAPI route
@app.post("/upload")
async def upload_link(data: LinkData):
    save_link(data.link)
    return {"status": "success", "message": "Link saved"}

# Run the FastAPI server when the script is executed
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8090, log_level="info")
