#!/usr/bin/env python3
"""
DoE-Assist Project Initialization Script
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run command and display results"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def create_directories():
    """Create necessary directory structure"""
    directories = [
        "logs",
        "data/raw",
        "data/processed", 
        "models/saved",
        "frontend/src/components",
        "frontend/src/pages",
        "frontend/src/services",
        "frontend/src/utils",
        "frontend/src/types",
        "backend/app/api",
        "backend/app/core",
        "backend/app/models",
        "backend/app/schemas",
        "backend/app/services",
        "backend/app/utils",
        "ml_engine/models",
        "ml_engine/features",
        "ml_engine/training",
        "ml_engine/prediction",
        "ml_engine/evaluation",
        "literature_mining/scrapers",
        "literature_mining/nlp",
        "literature_mining/extractors",
        "literature_mining/parsers",
        "literature_mining/storage",
        "database/models",
        "database/migrations",
        "database/seeds",
        "api/routes",
        "api/middleware",
        "tests/unit",
        "tests/integration",
        "tests/e2e"
    ]
    
    print("📁 Creating directory structure...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {directory}")
    
    print("✅ Directory structure creation completed")

def install_dependencies():
    """Install Python dependencies"""
    if run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("✅ Python dependencies installation completed")
    else:
        print("❌ Python dependencies installation failed")

def setup_git():
    """Initialize Git repository"""
    if not Path(".git").exists():
        run_command("git init", "Initializing Git repository")
        run_command("git add .", "Adding files to Git")
        run_command('git commit -m "Initial commit: Project structure setup"', "Initial commit")
        print("✅ Git repository initialization completed")
    else:
        print("ℹ️ Git repository already exists")

def create_gitignore():
    """Create .gitignore file"""
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Environment variables
.env
.env.local
.env.production

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Database
*.db
*.sqlite3

# Models
models/saved/*.pkl
models/saved/*.joblib
models/saved/*.h5

# Data
data/raw/*
data/processed/*
!data/raw/.gitkeep
!data/processed/.gitkeep

# Node modules
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build outputs
build/
dist/
*.tgz

# OS
.DS_Store
Thumbs.db
"""
    
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content.strip())
    print("✅ .gitignore file creation completed")

def main():
    """Main function"""
    print("🚀 Starting DoE-Assist project initialization...")
    print("=" * 50)
    
    # Create directory structure
    create_directories()
    print()
    
    # Create .gitignore
    create_gitignore()
    print()
    
    # Install dependencies
    install_dependencies()
    print()
    
    # Setup Git
    setup_git()
    print()
    
    print("🎉 Project initialization completed!")
    print("=" * 50)
    print("Next steps:")
    print("1. Copy config/env.example to .env and configure environment variables")
    print("2. Configure database connections")
    print("3. Run python scripts/start_services.py to start services")
    print("4. Visit http://localhost:3000 to view the frontend interface")

if __name__ == "__main__":
    main()
