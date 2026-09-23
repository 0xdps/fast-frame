"""Scaffold a customizable React admin interface."""

import os
import shutil
import sys
from argparse import ArgumentParser
from pathlib import Path


def add_arguments(parser: ArgumentParser) -> None:
    """Add command line arguments."""
    parser.add_argument(
        "path",
        nargs="?",
        default="admin-ui",
        help="Directory to create the admin interface in (default: admin-ui)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing directory if it exists"
    )


def execute(args) -> None:
    """Create the admin interface."""
    target_path = Path(getattr(args, 'path', 'admin-ui'))
    force = getattr(args, 'force', False)
    
    # Check if target directory exists
    if target_path.exists():
        if not force:
            print(
                f"Error: Directory '{target_path}' already exists. Use --force to overwrite.",
                file=sys.stderr,
            )
            return
        else:
            print(f"Removing existing directory '{target_path}'...")
            shutil.rmtree(target_path)
    
    # Get the template directory
    template_dir = Path(__file__).parent.parent.parent / "admin" / "templates" / "admin-ui"
    
    if not template_dir.exists():
        print(f"Error: Admin template not found at {template_dir}", file=sys.stderr)
        return
    
    try:
        # Copy the template
        print(f"Creating admin interface in '{target_path}'...")
        shutil.copytree(template_dir, target_path)
        
        # Make package.json executable scripts
        package_json_path = target_path / "package.json"
        if package_json_path.exists():
            os.chmod(package_json_path, 0o644)
        
        print("✓ Admin interface created successfully!")
        print("")
        print("Next steps:")
        print(f"  1. cd {target_path}")
        print("  2. npm install")
        print("  3. npm run dev")
        print("")
        print("The admin will be available at http://localhost:5173")
        print("")
        print("For production deployment:")
        print("  1. npm run build")
        print("  2. Serve the 'dist' folder from your FastAPI app")
        
    except Exception as e:
        print(f"Error creating admin interface: {e}", file=sys.stderr)
        if target_path.exists():
            shutil.rmtree(target_path)
        return