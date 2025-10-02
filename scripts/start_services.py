#!/usr/bin/env python3
"""
Script to start all services
"""
import subprocess
import time
import signal
import sys
import os
from pathlib import Path

class ServiceManager:
    def __init__(self):
        self.processes = []
        
    def start_service(self, name, command, cwd=None):
        """Start a service"""
        print(f"🚀 Starting {name}...")
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            self.processes.append((name, process))
            print(f"✅ {name} started (PID: {process.pid})")
            return process
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return None
    
    def stop_all_services(self):
        """Stop all services"""
        print("\n🛑 Stopping all services...")
        for name, process in self.processes:
            try:
                if os.name == 'nt':
                    process.terminate()
                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                print(f"✅ {name} stopped")
            except Exception as e:
                print(f"❌ Failed to stop {name}: {e}")
    
    def start_all_services(self):
        """Start all services"""
        print("🚀 Starting all DoE-Assist services...")
        print("=" * 50)
        
        # Check dependencies
        if not Path("requirements.txt").exists():
            print("❌ requirements.txt not found, please run setup_project.py first")
            return
        
        # Start backend API service
        self.start_service(
            "Backend API Service",
            "uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000",
            cwd="."
        )
        time.sleep(2)
        
        # Start literature mining service
        self.start_service(
            "Literature Mining Service", 
            "python -m literature_mining.api --host 0.0.0.0 --port 8001",
            cwd="."
        )
        time.sleep(2)
        
        # Start machine learning service
        self.start_service(
            "Machine Learning Service",
            "python -m ml_engine.api --host 0.0.0.0 --port 8002", 
            cwd="."
        )
        time.sleep(2)
        
        # Start frontend service (if exists)
        if Path("frontend/package.json").exists():
            self.start_service(
                "Frontend Service",
                "npm start",
                cwd="frontend"
            )
        
        print("\n✅ All services started successfully!")
        print("=" * 50)
        print("Service URLs:")
        print("🌐 Frontend Interface: http://localhost:3000")
        print("🔧 Backend API: http://localhost:8000")
        print("📚 Literature Mining API: http://localhost:8001") 
        print("🤖 Machine Learning API: http://localhost:8002")
        print("📖 API Documentation: http://localhost:8000/docs")
        print("\nPress Ctrl+C to stop all services")

def signal_handler(signum, frame):
    """Handle interrupt signal"""
    print("\n\nReceived interrupt signal, stopping services...")
    service_manager.stop_all_services()
    sys.exit(0)

def main():
    """Main function"""
    global service_manager
    service_manager = ServiceManager()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        service_manager.start_all_services()
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        service_manager.stop_all_services()

if __name__ == "__main__":
    main()
