#!/usr/bin/env python3
"""
Build and package script for The Football Life Engine AWS Lambda deployment.
Packages application code from `src/` and dependencies into a deployment zip.

Usage:
    python scripts/package_lambda.py [--output terraform/webapp/build/lambda_package.zip] [--skip-deps]
"""
import os
import sys
import shutil
import zipfile
import subprocess
import argparse
from pathlib import Path

def package_lambda(output_zip: str, skip_deps: bool = False):
    root_dir = Path(__file__).resolve().parent.parent
    output_path = Path(output_zip)
    if not output_path.is_absolute():
        output_path = root_dir / output_path

    build_dir = output_path.parent / "staging"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    print(f"📦 Packaging AWS Lambda deployment artifact...")
    print(f"   Root directory:   {root_dir}")
    print(f"   Staging directory: {build_dir}")
    print(f"   Target archive:   {output_path}")

    # 1. Install production dependencies into staging directory (unless skipped)
    requirements_file = root_dir / "requirements.txt"
    if not skip_deps and requirements_file.exists():
        print("📥 Installing runtime dependencies into staging...")
        cmd = [
            sys.executable, "-m", "pip", "install",
            "--target", str(build_dir),
            "--no-user",
            "--upgrade",
            "-r", str(requirements_file)
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("   ✓ Dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️ Dependency installation failed:\n{e.stderr}")
            print("   Proceeding with source packaging only.")

    # 2. Copy application source code into staging
    src_dir = root_dir / "src"
    target_src = build_dir / "src"
    if target_src.exists():
        shutil.rmtree(target_src)
    print("📁 Copying application source code (src/)...")
    shutil.copytree(src_dir, target_src, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
    print("   ✓ Application source code copied.")

    # 3. Create deployment zip archive
    print(f"🗜️  Creating deployment archive {output_path.name}...")
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in build_dir.rglob("*"):
            if file.is_file():
                rel_path = file.relative_to(build_dir)
                zf.write(file, arcname=str(rel_path).replace("\\", "/"))

    # Cleanup staging directory
    shutil.rmtree(build_dir, ignore_errors=True)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"✅ Lambda package built successfully! ({size_mb:.2f} MB)")
    print(f"   Location: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Package Football Life Engine for AWS Lambda")
    parser.add_argument(
        "--output",
        default="terraform/webapp/build/lambda_package.zip",
        help="Target zip archive file path"
    )
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip installing dependencies and package source code only"
    )
    args = parser.parse_args()
    package_lambda(args.output, args.skip_deps)
