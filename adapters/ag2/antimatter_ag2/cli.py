import os
import sys
import shutil
import argparse
from pathlib import Path
from antimatter_ag2 import server

def init_plugin():
    """Initializes the plugin by copying assets into the Antigravity IDE plugins directory."""
    print("Initializing Antimatter AG2 plugin...")
    
    home_dir = Path.home()
    plugin_dir = home_dir / ".gemini" / "config" / "plugins" / "antimatter-ag2"
    
    # Define source assets path
    assets_dir = Path(__file__).parent / "assets"
    
    if not assets_dir.exists():
        print(f"Error: Could not find assets directory at {assets_dir}", file=sys.stderr)
        sys.exit(1)
        
    try:
        # Create target directories
        print(f"Creating directory: {plugin_dir}")
        plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Copy plugin.json
        print("Copying plugin.json...")
        shutil.copy2(assets_dir / "plugin.json", plugin_dir / "plugin.json")
        
        # 2. Create skills directory and copy SKILL.md
        skill_dir = plugin_dir / "skills" / "antimatter-ag2"
        print(f"Creating directory: {skill_dir}")
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        print("Copying SKILL.md...")
        shutil.copy2(assets_dir / "skills" / "antimatter-ag2" / "SKILL.md", skill_dir / "SKILL.md")
        
        print("\n✅ Successfully initialized Antimatter AG2 Adapter!")
        print("You can now open Antigravity 2.0 and say: 'Start my Antimatter adapter'")
        
    except Exception as e:
        print(f"Failed to initialize plugin: {e}", file=sys.stderr)
        sys.exit(1)

def start_server():
    """Starts the WebSocket bridge adapter client in the background."""
    print("Starting Antimatter AG2 Adapter in background...")
    
    app_data = Path.home() / ".gemini" / "antigravity"
    app_data.mkdir(parents=True, exist_ok=True)
    pid_file = app_data / ".ag2.pid"
    
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text())
            os.kill(pid, 0)
            print("Adapter is already running.")
            return
        except (ValueError, OSError):
            pid_file.unlink(missing_ok=True)
            
    import subprocess
    
    process = subprocess.Popen(
        [sys.executable, "-m", "antimatter_ag2.cli", "run_server"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    
    pid_file.write_text(str(process.pid))
    print(f"✅ Adapter started successfully (PID: {process.pid}).")

def stop_server():
    """Stops the background adapter."""
    pid_file = Path.home() / ".gemini" / "antigravity" / ".ag2.pid"
    if not pid_file.exists():
        print("Adapter is not running.")
        return
        
    try:
        pid = int(pid_file.read_text())
        import signal
        os.kill(pid, signal.SIGTERM)
        print("Adapter stopped successfully.")
    except Exception as e:
        print(f"Failed to stop adapter or it was not running: {e}")
    finally:
        pid_file.unlink(missing_ok=True)

def run_server():
    """Actually runs the server loop (internal use)."""
    try:
        import asyncio
        asyncio.run(server.main())
    except KeyboardInterrupt:
        pass

def main():
    parser = argparse.ArgumentParser(description="Antimatter AG2 CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    subparsers.add_parser("init", help="Initialize the plugin in the Antigravity SDK directory")
    
    # Start command
    subparsers.add_parser("start", help="Start the WebSocket daemon in the background")
    
    # Stop command
    subparsers.add_parser("stop", help="Stop the background daemon")
    
    # Run server command (internal)
    subparsers.add_parser("run_server", help=argparse.SUPPRESS)
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_plugin()
    elif args.command == "start":
        start_server()
    elif args.command == "stop":
        stop_server()
    elif args.command == "run_server":
        run_server()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
