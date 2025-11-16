#!/usr/bin/env python3
"""
Cross-platform script to start Docker and automatically open browser
"""
import subprocess
import time
import sys
import platform
import webbrowser
import urllib.request
import urllib.error

def check_service_ready(url, max_retries=30, retry_interval=3):
    """Check if service is ready"""
    for i in range(max_retries):
        try:
            response = urllib.request.urlopen(url, timeout=2)
            if response.getcode() == 200:
                return True
        except (urllib.error.URLError, OSError):
            pass
        
        if i < max_retries - 1:
            print(f"Service not ready yet, waiting {retry_interval} seconds before retry... ({i+1}/{max_retries})")
            time.sleep(retry_interval)
    
    return False

def open_browser(url):
    """Open browser"""
    try:
        webbrowser.open(url)
        print(f"Opening browser: {url}")
        return True
    except Exception as e:
        print(f"Failed to open browser automatically: {e}")
        print(f"Please manually access: {url}")
        return False

def main():
    """Main function"""
    print("Starting Docker containers...")
    
    try:
        subprocess.run(
            ["docker-compose", "up", "-d"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Docker container startup command executed")
    except subprocess.CalledProcessError as e:
        print(f"Docker startup failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("docker-compose command not found, please ensure Docker Compose is installed")
        sys.exit(1)
    
    print("Waiting for services to be ready...")
    time.sleep(5)
    
    frontend_url = "http://localhost:3000"
    if check_service_ready(frontend_url):
        print("Frontend service is ready!")
        open_browser(frontend_url)
        
        print("\nDocker containers started, browser opened!")
        print(f"API Documentation: http://localhost:8000/docs")
        print(f"Backend API: http://localhost:8000")
        print("\nView logs: docker-compose logs -f")
        print("Stop services: docker-compose down")
    else:
        print("Service startup timeout, but containers may still be starting...")
        print(f"Please manually access: {frontend_url}")
        print("View logs: docker-compose logs -f")

if __name__ == "__main__":
    main()

