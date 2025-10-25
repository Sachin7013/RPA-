from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from api.rpa_api import router as rpa_router
import os
from pathlib import Path

app = FastAPI(title="AWS RPA Evidence Collection Tool", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create frontend directory if it doesn't exist
frontend_dir = Path("frontend")
frontend_dir.mkdir(exist_ok=True)

# ============================================================================
# CREATE EVIDENCE DIRECTORIES - EC2 Only
# ============================================================================
Path("evidence").mkdir(exist_ok=True)
Path("evidence/ec2_dashboard").mkdir(parents=True, exist_ok=True)
Path("evidence/ec2_instances").mkdir(parents=True, exist_ok=True)

# ============================================================================
# MOUNT STATIC FILES
# ============================================================================
app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/evidence", StaticFiles(directory="evidence"), name="evidence")

# Include API routes
app.include_router(
    rpa_router, prefix="/api", tags=["RPA"]
)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    html_file = Path("frontend/index.html")
    if html_file.exists():
        return FileResponse(html_file)
    else:
        # Return a basic HTML page if frontend doesn't exist yet
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AWS RPA Tool</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>AWS RPA Evidence Collection Tool</h1>
            <p>Frontend not yet configured. Please create frontend/index.html</p>
            <p>API is available at <a href="/docs">/docs</a></p>
        </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "AWS RPA Tool is running"}

if __name__ == "__main__":
    import uvicorn
    print("Starting AWS RPA Evidence Collection Tool...")
    print("Frontend: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
