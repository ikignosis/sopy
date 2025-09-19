from fastapi import FastAPI, HTTPException
import asyncio
import json
import socket
import os
from pathlib import Path

# Import the OpenAI router
from openai_router import router as openai_router

app = FastAPI()

# Include the OpenAI router
app.include_router(openai_router)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
def read_item(name: str):
    return {"message": f"Hello {name}"}

def send_admin_command(command):
    """Send a command to the admin socket and return the response."""
    socket_path = Path("/tmp/sopy_admin.sock")
    
    if not socket_path.exists():
        raise HTTPException(status_code=500, detail="Admin socket not available")
    
    try:
        # Create Unix socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(str(socket_path))
        
        # Send command
        sock.sendall(json.dumps(command).encode())
        
        # Receive response
        response = sock.recv(1024)
        sock.close()
        
        return json.loads(response.decode())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with admin socket: {e}")

# Authentication endpoints
@app.post("/admin/auth")
def add_auth(name: str, credentials: str):
    """Add authentication credentials via admin socket."""
    command = {
        "command": "add_auth",
        "name": name,
        "credentials": credentials
    }
    
    response = send_admin_command(command)
    
    if response["status"] == "success":
        return {"message": response["message"]}
    else:
        raise HTTPException(status_code=400, detail=response["message"])

@app.delete("/admin/auth/{name}")
def remove_auth(name: str):
    """Remove authentication credentials via admin socket."""
    command = {
        "command": "remove_auth",
        "name": name
    }
    
    response = send_admin_command(command)
    
    if response["status"] == "success":
        return {"message": response["message"]}
    else:
        raise HTTPException(status_code=400, detail=response["message"])

@app.get("/admin/auth")
def list_auth():
    """List all authentication names via admin socket."""
    command = {
        "command": "list_auth"
    }
    
    response = send_admin_command(command)
    
    if response["status"] == "success":
        return {"auth_names": response["auth_names"]}
    else:
        raise HTTPException(status_code=400, detail=response["message"])

@app.get("/admin/auth/{name}")
def get_auth(name: str):
    """Get authentication credentials via admin socket."""
    command = {
        "command": "get_auth",
        "name": name
    }
    
    response = send_admin_command(command)
    
    if response["status"] == "success":
        return {
            "name": response["name"],
            "credentials": response["credentials"]
        }
    else:
        raise HTTPException(status_code=400, detail=response["message"])

# Backend endpoints
@app.post("/admin/backend")
def add_backend(provider: str, url: str):
    """Add backend URL for a provider via admin socket."""
    command = {
        "command": "add_backend",
        "provider": provider,
        "url": url
    }
    
    response = send_admin_command(command)
    
    if response["status"] == "success":
        return {"message": response["message"]}
    else:
        raise HTTPException(status_code=400, detail=response["message"])

@app.delete("/admin/backend")
def remove_backend(provider: str, url: str):
    """Remove backend URL for a provider via admin socket."""
    command = {
        "command": "remove_backend",
        "provider": provider,
        "url": url
    }
    
    response = send_admin_command(command)
    
    if response["status"] == "success":
        return {"message": response["message"]}
    else:
        raise HTTPException(status_code=400, detail=response["message"])

@app.get("/admin/backend")
def list_backends():
    """List all providers and their backend URLs via admin socket."""
    command = {
        "command": "list_backends"
    }
    
    response = send_admin_command(command)
    
    if response["status"] == "success":
        return {"backends": response["backends"]}
    else:
        raise HTTPException(status_code=400, detail=response["message"])

@app.get("/admin/backend/{provider}")
def get_backend(provider: str):
    """Get backend URLs for a specific provider via admin socket."""
    command = {
        "command": "get_backend",
        "provider": provider
    }
    
    response = send_admin_command(command)
    
    if response["status"] == "success":
        return {
            "provider": response["provider"],
            "urls": response["urls"]
        }
    else:
        raise HTTPException(status_code=400, detail=response["message"])

# Model mapping endpoints
@app.post("/admin/model_mapping")
def add_model_mapping(model_name: str, provider: str):
    """Add model mapping to a provider via admin socket."""
    command = {
        "command": "add_model_mapping",
        "model_name": model_name,
        "provider": provider
    }
    
    response = send_admin_command(command)
    
    if response["status"] == "success":
        return {"message": response["message"]}
    else:
        raise HTTPException(status_code=400, detail=response["message"])

@app.delete("/admin/model_mapping/{model_name}")
def remove_model_mapping(model_name: str):
    """Remove model mapping to a provider via admin socket."""
    command = {
        "command": "remove_model_mapping",
        "model_name": model_name
    }
    
    response = send_admin_command(command)
    
    if response["status"] == "success":
        return {"message": response["message"]}
    else:
        raise HTTPException(status_code=400, detail=response["message"])

@app.get("/admin/model_mapping")
def list_model_mappings():
    """List all model mappings to providers via admin socket."""
    command = {
        "command": "list_model_mappings"
    }
    
    response = send_admin_command(command)
    
    if response["status"] == "success":
        return {"mappings": response["mappings"]}
    else:
        raise HTTPException(status_code=400, detail=response["message"])

@app.get("/admin/model_mapping/{model_name}")
def get_model_mapping(model_name: str):
    """Get provider for a specific model mapping via admin socket."""
    command = {
        "command": "get_model_mapping",
        "model_name": model_name
    }
    
    response = send_admin_command(command)
    
    if response["status"] == "success":
        return {
            "model_name": response["model_name"],
            "provider": response["provider"]
        }
    else:
        raise HTTPException(status_code=400, detail=response["message"])