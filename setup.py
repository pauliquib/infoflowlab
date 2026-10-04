"""
Setup script for InfoFlowLab
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="infoflowlab",
    version="1.0.0",
    author="pauliquib",
    description="Interactive simulator for compression and communication",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pauliquib/infoflowlab",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*", "docs"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Topic :: Education :: Computer Aided Instruction (CAI)",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PySide6>=6.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "Pillow>=10.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "full": [
            "PyQtGraph>=0.13.0",
            "numpy>=1.24.0",
            "Pillow>=10.0.0",
            "soundfile>=0.12.0",
            "scipy>=1.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "infoflowlab=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json"],
        "assets": ["*.png", "*.svg", "*.ico"],
    },
)