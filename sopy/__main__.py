import sys
from .start_server import start_server
from .stop_server import stop_server

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m sopy {start|stop}")
        sys.exit(1)
    
    if sys.argv[1] == "start":
        sys.exit(start_server())
    elif sys.argv[1] == "stop":
        sys.exit(stop_server())
    else:
        print(f"Unknown command: {sys.argv[1]}")
        print("Usage: python -m sopy {start|stop}")
        sys.exit(1)

if __name__ == "__main__":
    main()