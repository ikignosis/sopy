#!/usr/bin/env python3
"""
OpenAI-compatible router for FastAPI.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import httpx

# Create router
router = APIRouter(prefix="/v1")

# In-memory storage for registered models and their backends
registered_models = {}

def update_registered_models(model_backends):
    """
    Update the registered models with the current model to backend mappings.
    This function should be called by the admin socket server when backends or model mappings are added or removed.
    """
    # Clear existing registered models
    registered_models.clear()
    
    # Register models with their backend URLs
    for model_name, backend_url in model_backends.items():
        register_model(model_name, backend_url)
    
    print(f"Updated registered models: {registered_models}")

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 150
    stream: Optional[bool] = False

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

@router.post("/chat/completions")
async def chat_completions(request: Request, chat_request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.
    """
    print(f"chat_completions called for model: {chat_request.model}, registered_models: {registered_models}")  # Debug print
    # Check if we have a backend for this model
    if chat_request.model not in registered_models:
        raise HTTPException(
            status_code=404, 
            detail=f"Model '{chat_request.model}' not found"
        )
    
    # Get backend URL for this model
    backend_url = registered_models[chat_request.model]
    
    # Forward request to backend
    try:
        async with httpx.AsyncClient() as client:
            # Prepare the request for the backend
            backend_request = {
                "model": chat_request.model,
                "messages": chat_request.messages,
                "temperature": chat_request.temperature,
                "max_tokens": chat_request.max_tokens,
                "stream": chat_request.stream
            }
            
            # Get authorization header from incoming request
            auth_header = request.headers.get("Authorization")
            
            # Prepare headers for backend request
            backend_headers = {"Content-Type": "application/json"}
            if auth_header:
                backend_headers["Authorization"] = auth_header
            
            # Send request to backend
            response = await client.post(
                f"{backend_url}/chat/completions",  # Removed /v1 from the URL since it's already in the backend_url
                json=backend_request,
                headers=backend_headers
            )
            
            # Log the response for debugging
            print(f"Backend response status: {response.status_code}")
            print(f"Backend response headers: {dict(response.headers)}")
            print(f"Backend response text: {response.text}")
            
            # Try to parse and return the response
            try:
                json_response = response.json()
                print("Successfully parsed JSON response")
                return json_response
            except Exception as e:
                print(f"Error parsing response as JSON: {e}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Error parsing backend response: {str(e)}"
                )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error forwarding request to backend: {str(e)}"
        )

@router.get("/models")
async def list_models():
    """
    List all available models.
    """
    print(f"list_models called, registered_models: {registered_models}")  # Debug print
    return {
        "object": "list",
        "data": [
            {
                "id": model_name,
                "object": "model",
                "created": 1677610602,
                "owned_by": "sopy"
            }
            for model_name in registered_models.keys()
        ]
    }

def register_model(model_name: str, backend_url: str):
    """
    Register a model with its backend URL.
    This function would typically be called by the admin socket server
    when backends are added.
    """
    registered_models[model_name] = backend_url

def unregister_model(model_name: str):
    """
    Unregister a model.
    This function would typically be called by the admin socket server
    when backends are removed.
    """
    if model_name in registered_models:
        del registered_models[model_name]