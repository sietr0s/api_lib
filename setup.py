from setuptools import setup, find_packages
from pathlib import Path
import sys

def read_file(filename):
    """Read a text file and return its contents."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Fallback for files that might have different encoding
        with open(filename, 'r', encoding='utf-8-sig') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {filename}: {str(e)}", file=sys.stderr)
        return ""

def get_requirements():
    """Return list of requirements from requirements.txt."""
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as fh:
            return [
                line.strip()
                for line in fh
                if line.strip() and not line.startswith("#")
            ]
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        with open('requirements.txt', 'r', encoding='utf-8-sig') as fh:
            return [
                line.strip()
                for line in fh
                if line.strip() and not line.startswith("#")
            ]
    except FileNotFoundError:
        return []

# Read long description from README.md
long_description = read_file("README.md") or "A FastAPI CRUD library with dependency injection"

setup(
    name="api-lib",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A FastAPI CRUD library with dependency injection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/api-lib",
    packages=find_packages(exclude=["tests*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: FastAPI",
    ],
    python_requires=">=3.8",
    install_requires=get_requirements(),
    include_package_data=True,
    zip_safe=False,
    project_urls={
        "Bug Reports": "https://github.com/yourusername/api-lib/issues",
        "Source": "https://github.com/yourusername/api-lib",
    },
)