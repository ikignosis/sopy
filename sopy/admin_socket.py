#!/usr/bin/env python3
"""
Admin socket module for managing authentication credentials and backend URLs via Unix socket.
"""
import asyncio
import json
import os
import socket
import sys
import sqlite3
from pathlib import Path

# Import the OpenAI router to update registered models
from sopy.openai_router import update_registered_models

# Socket path for admin commands
ADMIN_SOCKET_PATH = Path("/tmp/sopy_admin.sock")  # Unix socket path (not used on Windows)
ADMIN_HOST = "127.0.0.1"  # TCP host for Windows compatibility
ADMIN_PORT = 8001  # TCP port for Windows compatibility
# Database path
DB_PATH = Path("sopy_admin.db")

class AdminSocketServer:
    def __init__(self):
        self.socket_path = ADMIN_SOCKET_PATH
        self.server = None
        self.db_path = DB_PATH
        self.init_database()
        
    async def update_openai_router(self):
        """Update the OpenAI router with current backends and model mappings."""
        try:
            # Get all backends from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT provider, url FROM backends")
            backend_rows = cursor.fetchall()
            
            # Get all model mappings from database
            cursor.execute("SELECT model_name, provider FROM model_mappings")
            mapping_rows = cursor.fetchall()
            conn.close()
            
            # Organize backends by provider
            backends = {}
            for provider, url in backend_rows:
                if provider not in backends:
                    backends[provider] = []
                backends[provider].append(url)
            
            # Create model to backend URL mapping
            model_backends = {}
            for model_name, provider in mapping_rows:
                # Get the first backend URL for the provider
                if provider in backends and backends[provider]:
                    model_backends[model_name] = backends[provider][0]
            
            # Update registered models in the OpenAI router
            update_registered_models(model_backends)
        except Exception as e:
            print(f"Error updating OpenAI router: {e}")
        
    def init_database(self):
        """Initialize the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create admin credentials table (for backend providers)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_credentials (
                name TEXT PRIMARY KEY,
                credentials TEXT NOT NULL
            )
        ''')
        
        # Create user API keys table (for client-facing API keys)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # If the old credentials table exists and user_api_keys doesn't, migrate data
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='credentials'")
        if cursor.fetchone() and not cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_api_keys'").fetchone():
            print("Migrating from old credentials table to admin_credentials...")
            cursor.execute("INSERT OR REPLACE INTO admin_credentials SELECT * FROM credentials")
            cursor.execute("DROP TABLE credentials")
            print("Migration completed.")
        
        # Create backends table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                url TEXT NOT NULL,
                UNIQUE(provider, url)
            )
        ''')
        
        # Create model mappings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_mappings (
                model_name TEXT PRIMARY KEY,
                provider TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Update OpenAI router with existing backends and model mappings
        asyncio.create_task(self.update_openai_router())
        
    async def start_server(self):
        """Start the server for admin commands (Unix socket on Unix, TCP socket on Windows)."""
        if os.name == 'nt':  # Windows
            # Use TCP socket on Windows
            self.server = await asyncio.start_server(
                self.handle_client,
                host=ADMIN_HOST,
                port=ADMIN_PORT
            )
            print(f"Admin TCP server started at {ADMIN_HOST}:{ADMIN_PORT}")
        else:  # Unix-like systems
            # Use Unix socket on Unix-like systems
            # Remove existing socket file if it exists
            if self.socket_path.exists():
                self.socket_path.unlink()
                
            self.server = await asyncio.start_unix_server(
                self.handle_client, 
                path=str(self.socket_path)
            )
            
            # Set proper permissions (owner read/write only)
            os.chmod(self.socket_path, 0o600)
            
            print(f"Admin socket server started at {self.socket_path}")
        
        async with self.server:
            await self.server.serve_forever()
            
    async def handle_client(self, reader, writer):
        """Handle incoming client connections."""
        try:
            # Read command
            data = await reader.read(1024)
            if not data:
                return
                
            try:
                command = json.loads(data.decode())
            except json.JSONDecodeError:
                response = {"status": "error", "message": "Invalid JSON"}
                writer.write(json.dumps(response).encode())
                await writer.drain()
                writer.close()
                await writer.wait_closed()
                return
                
            # Process command
            response = await self.process_command(command)
            
            # Send response
            writer.write(json.dumps(response).encode())
            await writer.drain()
            
        except Exception as e:
            response = {"status": "error", "message": str(e)}
            writer.write(json.dumps(response).encode())
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
            
    async def process_command(self, command):
        """Process admin commands."""
        cmd_type = command.get("command")
        
        # Admin authentication commands (for backend providers)
        if cmd_type == "add_admin_auth":
            return await self.add_admin_auth(command)
        elif cmd_type == "remove_admin_auth":
            return await self.remove_admin_auth(command)
        elif cmd_type == "list_admin_auth":
            return await self.list_admin_auth(command)
        elif cmd_type == "get_admin_auth":
            return await self.get_admin_auth(command)
        
        # User API key commands (for client-facing API keys)
        elif cmd_type == "add_user_api_key":
            return await self.add_user_api_key(command)
        elif cmd_type == "remove_user_api_key":
            return await self.remove_user_api_key(command)
        elif cmd_type == "list_user_api_keys":
            return await self.list_user_api_keys(command)
        elif cmd_type == "get_user_api_key":
            return await self.get_user_api_key(command)
        elif cmd_type == "activate_user_api_key":
            return await self.activate_user_api_key(command)
        elif cmd_type == "deactivate_user_api_key":
            return await self.deactivate_user_api_key(command)
        # Backend commands
        elif cmd_type == "add_backend":
            return await self.add_backend(command)
        elif cmd_type == "remove_backend":
            return await self.remove_backend(command)
        elif cmd_type == "list_backends":
            return await self.list_backends(command)
        elif cmd_type == "get_backend":
            return await self.get_backend(command)
        # Model mapping commands
        elif cmd_type == "add_model_mapping":
            return await self.add_model_mapping(command)
        elif cmd_type == "remove_model_mapping":
            return await self.remove_model_mapping(command)
        elif cmd_type == "list_model_mappings":
            return await self.list_model_mappings(command)
        elif cmd_type == "get_model_mapping":
            return await self.get_model_mapping(command)
        else:
            return {"status": "error", "message": f"Unknown command: {cmd_type}"}
            
    async def add_admin_auth(self, command):
        """Add admin authentication credentials (for backend providers)."""
        try:
            name = command["name"]
            credentials = command["credentials"]
            
            # Store credentials in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO admin_credentials (name, credentials) VALUES (?, ?)",
                (name, credentials)
            )
            conn.commit()
            conn.close()
            
            return {
                "status": "success", 
                "message": f"Authentication credentials for '{name}' added successfully"
            }
        except KeyError as e:
            return {"status": "error", "message": f"Missing required field: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}
            
    async def remove_admin_auth(self, command):
        """Remove admin authentication credentials (for backend providers)."""
        try:
            name = command["name"]
            
            # Remove credentials from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admin_credentials WHERE name = ?", (name,))
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if deleted:
                return {
                    "status": "success", 
                    "message": f"Authentication credentials for '{name}' removed"
                }
            else:
                return {
                    "status": "error", 
                    "message": f"No credentials found for '{name}'"
                }
        except KeyError as e:
            return {"status": "error", "message": f"Missing required field: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}
            
    async def list_admin_auth(self, command):
        """List all admin authentication names (without credentials)."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM admin_credentials")
            auth_names = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return {
                "status": "success",
                "auth_names": auth_names
            }
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}
        
    async def get_admin_auth(self, command):
        """Get admin authentication credentials by name."""
        try:
            name = command["name"]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT credentials FROM admin_credentials WHERE name = ?", (name,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "status": "success",
                    "name": name,
                    "credentials": row[0]
                }
            else:
                return {
                    "status": "error", 
                    "message": f"No credentials found for '{name}'"
                }
        except KeyError as e:
            return {"status": "error", "message": f"Missing required field: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}
            

    async def add_user_api_key(self, command):
        """Add a user-facing API key."""
        try:
            api_key = command.get("api_key")
            description = command.get("description", "")
            
            if not api_key:
                return {"status": "error", "message": "API key is required"}
            
            # Store API key in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_api_keys (api_key, description) VALUES (?, ?)",
                (api_key, description)
            )
            conn.commit()
            conn.close()
            
            return {
                "status": "success", 
                "message": f"User API key added successfully"
            }
        except sqlite3.IntegrityError:
            return {"status": "error", "message": "API key already exists"}
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}

    async def remove_user_api_key(self, command):
        """Remove a user-facing API key."""
        try:
            api_key = command["api_key"]
            
            # Remove API key from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_api_keys WHERE api_key = ?", (api_key,))
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if deleted:
                return {
                    "status": "success", 
                    "message": f"User API key removed"
                }
            else:
                return {
                    "status": "error", 
                    "message": f"No user API key found"
                }
        except KeyError as e:
            return {"status": "error", "message": f"Missing required field: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}

    async def list_user_api_keys(self, command):
        """List all user-facing API keys."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, api_key, description, created_at, is_active FROM user_api_keys")
            keys = []
            for row in cursor.fetchall():
                keys.append({
                    "id": row[0],
                    "api_key": row[1],
                    "description": row[2],
                    "created_at": row[3],
                    "is_active": bool(row[4])
                })
            conn.close()
            
            return {
                "status": "success",
                "user_api_keys": keys
            }
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}

    async def get_user_api_key(self, command):
        """Get a user-facing API key by ID."""
        try:
            key_id = command["id"]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, api_key, description, created_at, is_active FROM user_api_keys WHERE id = ?", (key_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "status": "success",
                    "user_api_key": {
                        "id": row[0],
                        "api_key": row[1],
                        "description": row[2],
                        "created_at": row[3],
                        "is_active": bool(row[4])
                    }
                }
            else:
                return {
                    "status": "error", 
                    "message": f"No user API key found with ID {key_id}"
                }
        except KeyError as e:
            return {"status": "error", "message": f"Missing required field: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}

    async def activate_user_api_key(self, command):
        """Activate a user-facing API key."""
        try:
            key_id = command["id"]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE user_api_keys SET is_active = 1 WHERE id = ?", (key_id,))
            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if updated:
                return {
                    "status": "success", 
                    "message": f"User API key activated"
                }
            else:
                return {
                    "status": "error", 
                    "message": f"No user API key found with ID {key_id}"
                }
        except KeyError as e:
            return {"status": "error", "message": f"Missing required field: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}

    async def deactivate_user_api_key(self, command):
        """Deactivate a user-facing API key."""
        try:
            key_id = command["id"]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE user_api_keys SET is_active = 0 WHERE id = ?", (key_id,))
            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if updated:
                return {
                    "status": "success", 
                    "message": f"User API key deactivated"
                }
            else:
                return {
                    "status": "error", 
                    "message": f"No user API key found with ID {key_id}"
                }
        except KeyError as e:
            return {"status": "error", "message": f"Missing required field: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}

    async def add_backend(self, command):
        """Add backend URL for a provider."""
        try:
            provider = command["provider"]
            url = command["url"]
            
            # Store backend URL in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO backends (provider, url) VALUES (?, ?)",
                (provider, url)
            )
            conn.commit()
            conn.close()
            
            # Update registered models in the OpenAI router
            await self.update_openai_router()
            
            return {
                "status": "success", 
                "message": f"Backend URL for '{provider}' added successfully"
            }
        except KeyError as e:
            return {"status": "error", "message": f"Missing required field: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}
            
    async def add_model_mapping(self, command):
        """Add model mapping to a provider."""
        try:
            model_name = command["model_name"]
            provider = command["provider"]
            
            # Store model mapping in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO model_mappings (model_name, provider) VALUES (?, ?)",
                (model_name, provider)
            )
            conn.commit()
            conn.close()
            
            # Update registered models in the OpenAI router
            await self.update_openai_router()
            
            return {
                "status": "success", 
                "message": f"Model '{model_name}' mapped to provider '{provider}' successfully"
            }
        except KeyError as e:
            return {"status": "error", "message": f"Missing required field: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}
            
    async def remove_backend(self, command):
        """Remove backend URL for a provider."""
        try:
            provider = command["provider"]
            url = command["url"]
            
            # Remove backend URL from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM backends WHERE provider = ? AND url = ?", (provider, url))
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            # Update registered models in the OpenAI router
            if deleted:
                await self.update_openai_router()
                return {
                    "status": "success", 
                    "message": f"Backend URL for '{provider}' removed"
                }
            else:
                return {
                    "status": "error", 
                    "message": f"No backend URL found for '{provider}'"
                }
        except KeyError as e:
            return {"status": "error", "message": f"Missing required field: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}
            
    async def remove_model_mapping(self, command):
        """Remove model mapping to a provider."""
        try:
            model_name = command["model_name"]
            
            # Remove model mapping from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM model_mappings WHERE model_name = ?", (model_name,))
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            # Update registered models in the OpenAI router
            if deleted:
                await self.update_openai_router()
                return {
                    "status": "success", 
                    "message": f"Model mapping for '{model_name}' removed"
                }
            else:
                return {
                    "status": "error", 
                    "message": f"No model mapping found for '{model_name}'"
                }
        except KeyError as e:
            return {"status": "error", "message": f"Missing required field: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}
            
    async def list_backends(self, command):
        """List all providers and their backend URLs."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all backends from database
            cursor.execute("SELECT provider, url FROM backends")
            rows = cursor.fetchall()
            
            # Organize backends by provider
            backends = {}
            for provider, url in rows:
                if provider not in backends:
                    backends[provider] = []
                backends[provider].append(url)
            
            conn.close()
            
            return {
                "status": "success",
                "backends": backends
            }
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}
            
    async def list_model_mappings(self, command):
        """List all model mappings to providers."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all model mappings from database
            cursor.execute("SELECT model_name, provider FROM model_mappings")
            rows = cursor.fetchall()
            
            # Organize mappings
            mappings = {}
            for model_name, provider in rows:
                mappings[model_name] = provider
            
            conn.close()
            
            return {
                "status": "success",
                "mappings": mappings
            }
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}
        
    async def get_backend(self, command):
        """Get backend URLs for a specific provider."""
        try:
            provider = command["provider"]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT url FROM backends WHERE provider = ?", (provider,))
            urls = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if urls:
                return {
                    "status": "success",
                    "provider": provider,
                    "urls": urls
                }
            else:
                return {
                    "status": "error", 
                    "message": f"No backends found for '{provider}'"
                }
        except KeyError as e:
            return {"status": "error", "message": f"Missing required field: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}
            
    async def get_model_mapping(self, command):
        """Get provider for a specific model mapping."""
        try:
            model_name = command["model_name"]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT provider FROM model_mappings WHERE model_name = ?", (model_name,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "status": "success",
                    "model_name": model_name,
                    "provider": row[0]
                }
            else:
                return {
                    "status": "error", 
                    "message": f"No mapping found for model '{model_name}'"
                }
        except KeyError as e:
            return {"status": "error", "message": f"Missing required field: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}

async def main():
    """Main entry point for the admin socket server."""
    server = AdminSocketServer()
    try:
        await server.start_server()
    except KeyboardInterrupt:
        print("Admin socket server stopped")
    except Exception as e:
        print(f"Error starting admin socket server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())