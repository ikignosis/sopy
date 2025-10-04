#!/usr/bin/env python3
"""
Script to stop the Sopy server processes.
"""
import os
import sys
import signal
import psutil
import argparse
from pathlib import Path

def find_server_processes():
    """Find the Sopy server processes by name."""
    main_process = None
    admin_process = None
    
    # Look for processes with sopy.main or sopy.admin_socket in the command line
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            if proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'sopy.main' in cmdline and 'uvicorn' in cmdline:
                    main_process = proc
                elif 'sopy.admin_socket' in cmdline:
                    admin_process = proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return main_process, admin_process

def stop_server():
    """Stop the Sopy server processes."""
    print("\U0001F50D Searching for Sopy server processes...")
    
    main_process, admin_process = find_server_processes()
    
    stopped_any = False
    
    if main_process:
        try:
            main_process.terminate()
            main_process.wait(timeout=5)
            print(f"\u2705 Main server (PID: {main_process.pid}) stopped successfully")
            stopped_any = True
        except psutil.TimeoutExpired:
            print(f"\u26A0\uFE0F Main server (PID: {main_process.pid}) did not stop gracefully, forcing termination")
            main_process.kill()
            print(f"\u2705 Main server (PID: {main_process.pid}) forcefully terminated")
            stopped_any = True
        except Exception as e:
            print(f"\u274C Error stopping main server (PID: {main_process.pid}): {e}")
    
    if admin_process:
        try:
            admin_process.terminate()
            admin_process.wait(timeout=5)
            print(f"\u2705 Admin socket server (PID: {admin_process.pid}) stopped successfully")
            stopped_any = True
        except psutil.TimeoutExpired:
            print(f"\u26A0\uFE0F Admin socket server (PID: {admin_process.pid}) did not stop gracefully, forcing termination")
            admin_process.kill()
            print(f"\u2705 Admin socket server (PID: {admin_process.pid}) forcefully terminated")
            stopped_any = True
        except Exception as e:
            print(f"\u274C Error stopping admin socket server (PID: {admin_process.pid}): {e}")
    
    if not stopped_any:
        print("\u2139\uFE0F No Sopy server processes found")
        return 1
    
    return 0

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Stop the Sopy server processes")
    parser.add_argument("-f", "--force", action="store_true", help="Force termination of processes")
    
    args = parser.parse_args()
    
    try:
        return stop_server()
    except KeyboardInterrupt:
        print("\n\U0001F6D1 Stopping server termination (interrupted by user)")
        return 1
    except Exception as e:
        print(f"\u274C Error stopping server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())