#!/usr/bin/env python3
"""
Project completeness checker for DoE-Assist
"""
import os
from pathlib import Path

def check_directory_structure():
    """Check if all required directories exist"""
    required_dirs = [
        "frontend/src",
        "frontend/src/components",
        "frontend/src/pages",
        "frontend/src/services",
        "frontend/src/utils",
        "frontend/src/types",
        "frontend/src/styles",
        "frontend/public",
        "backend/app",
        "backend/app/api",
        "backend/app/core",
        "backend/app/models",
        "backend/app/schemas",
        "backend/app/services",
        "backend/app/utils",
        "backend/alembic",
        "backend/tests",
        "database/models",
        "database/migrations",
        "database/seeds",
        "database/scripts",
        "ml_engine/models",
        "ml_engine/features",
        "ml_engine/training",
        "ml_engine/prediction",
        "ml_engine/evaluation",
        "ml_engine/utils",
        "literature_mining/scrapers",
        "literature_mining/nlp",
        "literature_mining/extractors",
        "literature_mining/parsers",
        "literature_mining/storage",
        "api/routes",
        "api/middleware",
        "api/auth",
        "api/gateway",
        "api/docs",
        "tests/unit",
        "tests/integration",
        "tests/e2e",
        "tests/fixtures",
        "tests/data",
        "config",
        "docs",
        "scripts"
    ]
    
    missing_dirs = []
    for directory in required_dirs:
        if not Path(directory).exists():
            missing_dirs.append(directory)
    
    return missing_dirs

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        "README.md",
        "requirements.txt",
        "frontend/README.md",
        "frontend/package.json",
        "frontend/src/App.tsx",
        "frontend/src/index.tsx",
        "frontend/src/pages/HomePage.tsx",
        "frontend/src/pages/ParameterQueryPage.tsx",
        "frontend/src/pages/DataInputPage.tsx",
        "frontend/src/pages/ResultsDisplayPage.tsx",
        "frontend/src/pages/FeedbackPage.tsx",
        "frontend/public/index.html",
        "backend/README.md",
        "backend/app/main.py",
        "database/README.md",
        "ml_engine/README.md",
        "literature_mining/README.md",
        "api/README.md",
        "tests/README.md",
        "config/database.yaml",
        "config/api.yaml",
        "config/env.example",
        "docs/TEAM_ASSIGNMENT.md",
        "scripts/setup_project.py",
        "scripts/start_services.py",
        "scripts/check_project.py",
        "Dockerfile",
        "docker-compose.yml"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    return missing_files

def main():
    """Main function to check project completeness"""
    print("🔍 Checking DoE-Assist project completeness...")
    print("=" * 50)
    
    # Check directories
    print("📁 Checking directory structure...")
    missing_dirs = check_directory_structure()
    if missing_dirs:
        print("❌ Missing directories:")
        for directory in missing_dirs:
            print(f"   - {directory}")
    else:
        print("✅ All required directories exist")
    
    print()
    
    # Check files
    print("📄 Checking required files...")
    missing_files = check_required_files()
    if missing_files:
        print("❌ Missing files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
    else:
        print("✅ All required files exist")
    
    print()
    
    # Summary
    if not missing_dirs and not missing_files:
        print("🎉 Project is complete and ready for development!")
        print("=" * 50)
        print("Next steps:")
        print("1. Copy config/env.example to .env and configure environment variables")
        print("2. Run 'python scripts/setup_project.py' to initialize the project")
        print("3. Each team member can start working on their assigned module")
        print("4. Use 'python scripts/start_services.py' to start all services")
    else:
        print("⚠️  Project setup incomplete. Please address the missing items above.")
    
    return len(missing_dirs) + len(missing_files) == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
