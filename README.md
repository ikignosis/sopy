# Sopy - OpenAI-Compatible API Gateway

Sopy is an OpenAI-compatible API gateway that routes requests to different backend providers. It provides a unified interface for accessing various AI models while maintaining compatibility with the OpenAI API specification.

## Features

- OpenAI-compatible API endpoints
- Dynamic backend routing based on model names
- Unix socket-based admin interface for configuration
- SQLite database for persistent storage of credentials and backends
- FastAPI-based implementation for high performance

## Installation

```bash
pip install -r requirements.txt
```

## Running the Application

### Option 1: Using the start script (recommended)

```bash
python start_server.py
```

This will start both the main server and the admin socket server in the background and provide you with:

- Server URL
- Process IDs (PIDs) for easy stopping
- Log file location

### Option 2: Manual start

```bash
# Start the admin socket server
python admin_socket.py &

# Start the main FastAPI server
uvicorn main:app --reload
```

## API Endpoints

### Main Endpoints

- `GET /` - Returns a simple "Hello World" message
- `GET /hello/{name}` - Returns a personalized greeting

### OpenAI-Compatible Endpoints

- `POST /v1/chat/completions` - Chat completions endpoint
- `GET /v1/models` - List available models

### Admin Endpoints (via Unix socket)

#### Admin Authentication management (for backend providers):

- `POST /admin/admin_auth` - Add admin authentication credentials
- `DELETE /admin/admin_auth/{name}` - Remove admin authentication credentials
- `GET /admin/admin_auth` - List all admin authentication names
- `GET /admin/admin_auth/{name}` - Get admin authentication credentials

#### User API Key management (for client-facing API keys):

- `POST /admin/user_api_key` - Add user API key
- `DELETE /admin/user_api_key` - Remove user API key
- `GET /admin/user_api_keys` - List all user API keys
- `GET /admin/user_api_key/{id}` - Get user API key by ID
- `PUT /admin/user_api_key/activate/{id}` - Activate user API key
- `PUT /admin/user_api_key/deactivate/{id}` - Deactivate user API key

#### Backend management:

- `POST /admin/backend` - Add backend URL for a provider
- `DELETE /admin/backend` - Remove backend URL for a provider
- `GET /admin/backend` - List all providers and their backend URLs
- `GET /admin/backend/{provider}` - Get backend URLs for a specific provider

#### Model mapping management:

- `POST /admin/model_mapping` - Add model mapping to a provider
- `DELETE /admin/model_mapping/{model_name}` - Remove model mapping to a provider
- `GET /admin/model_mapping` - List all model mappings to providers
- `GET /admin/model_mapping/{model_name}` - Get provider for a specific model mapping

## Database

Sopy uses SQLite for persistent storage of credentials and backend configurations. The database file is automatically created as `sopy_admin.db` in the application directory.

## Testing the API

Once the server is running, you can test the endpoints:

```bash
# Test the root endpoint
curl http://localhost:8000/

# Test the personalized greeting
curl http://localhost:8000/hello/Alice

# Test the OpenAI-compatible chat completions endpoint
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Test the models endpoint
curl http://localhost:8000/v1/models
```

Or visit the interactive API documentation at `http://localhost:8000/docs`

## Admin Socket Commands

The admin socket uses JSON messages for communication. Here are examples of commands you can send:

### Add Admin Authentication Credentials

```json
{
  "command": "add_admin_auth",
  "name": "openai",
  "credentials": "sk-..."
}
```

### Remove Admin Authentication Credentials

```json
{
  "command": "remove_admin_auth",
  "name": "openai"
}
```

### List Admin Authentication Names

```json
{
  "command": "list_admin_auth"
}
```

### Get Admin Authentication Credentials

```json
{
  "command": "get_admin_auth",
  "name": "openai"
}
```

### Add User API Key

```json
{
  "command": "add_user_api_key",
  "api_key": "sk-user-123",
  "description": "Test user API key"
}
```

### Remove User API Key

```json
{
  "command": "remove_user_api_key",
  "api_key": "sk-user-123"
}
```

### List User API Keys

```json
{
  "command": "list_user_api_keys"
}
```

### Get User API Key by ID

```json
{
  "command": "get_user_api_key",
  "id": 1
}
```

### Activate User API Key

```json
{
  "command": "activate_user_api_key",
  "id": 1
}
```

### Deactivate User API Key

```json
{
  "command": "deactivate_user_api_key",
  "id": 1
}
```

### Add Backend URL

```json
{
  "command": "add_backend",
  "provider": "openai",
  "url": "https://api.openai.com"
}
```

### Remove Backend URL

```json
{
  "command": "remove_backend",
  "provider": "openai",
  "url": "https://api.openai.com"
}
```

### List All Backends

```json
{
  "command": "list_backends"
}
```

### Get Backends for a Provider

```json
{
  "command": "get_backend",
  "provider": "openai"
}
```

### Add Model Mapping

```json
{
  "command": "add_model_mapping",
  "model_name": "gpt-4.1",
  "provider": "openai"
}
```

### Remove Model Mapping

```json
{
  "command": "remove_model_mapping",
  "model_name": "gpt-4.1"
}
```

### List All Model Mappings

```json
{
  "command": "list_model_mappings"
}
```

### Get Provider for a Model

```json
{
  "command": "get_model_mapping",
  "model_name": "gpt-4.1"
}
```

## Stopping the Server

If you used the start script, you can stop the servers using the PIDs provided:

```bash
kill <MAIN_PID> <ADMIN_PID>
```

Replace `<MAIN_PID>` and `<ADMIN_PID>` with the actual process IDs shown when starting the server.