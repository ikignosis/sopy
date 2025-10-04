#!/usr/bin/env python3
import subprocess
import os
import sys
import time
import signal
from pathlib import Path

def start_server():
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Generate logfile name with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    logfile = logs_dir / f"server_{timestamp}.log"
    
    # Server details
    host = "127.0.0.1"
    port = 8000
    url = f"http://{host}:{port}"
    
    print(f"🚀 Starting FastAPI server...")
    print(f"📍 URL: {url}")
    print(f"📋 Log file: {logfile}")
    
    # Start the admin socket server in background
    try:
        admin_process = subprocess.Popen(
            [sys.executable, "-m", "sopy.admin_socket"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Give the admin socket server a moment to start
        time.sleep(1)
        
        # Check if admin process is still running
        if admin_process.poll() is not None:
            print("❌ Admin socket server failed to start")
            return 1
            
        print(f"✅ Admin socket server started (PID: {admin_process.pid})")
        
    except Exception as e:
        print(f"❌ Error starting admin socket server: {e}")
        return 1
    
    # Start the main FastAPI server in background
    try:
        with open(logfile, 'w') as f:
            process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "sopy.main:app", "--host", host, "--port", str(port)],
                stdout=f,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
        
        # Give the server a moment to start
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"✅ Main server started successfully!")
            print(f"🆔 Main server PID: {process.pid}")
            print(f"🆔 Admin socket server PID: {admin_process.pid}")
            print(f"📝 Logs are being written to: {logfile}")
            print(f"\n💡 To stop the servers, run: kill {process.pid} {admin_process.pid}")
            print(f"💡 To view logs in real-time, run: tail -f {logfile}")
            print(f"\n🌐 Visit {url}/docs for interactive API documentation")
        else:
            print(f"❌ Main server failed to start. Check logs: {logfile}")
            # Kill the admin socket server if main server failed
            admin_process.terminate()
            return 1
            
    except Exception as e:
        print(f"❌ Error starting main server: {e}")
        # Kill the admin socket server if main server failed
        admin_process.terminate()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(start_server())