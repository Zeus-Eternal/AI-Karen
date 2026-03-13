"""
Setup script for Kari Extensions SDK.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text().strip().split('\n')

setup(
    name="kari-extensions-sdk",
    version="1.0.0",
    description="SDK for developing Kari AI extensions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Kari AI Team",
    author_email="developers@kari.ai",
    url="https://github.com/kari-ai/extensions-sdk",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "core.extensions.sdk": ["templates/**/*"],
    },
    install_requires=[
        "click>=8.0.0",
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "pydantic>=1.8.0",
        "requests>=2.25.0",
        "jsonschema>=3.2.0",
        "watchdog>=2.1.0",
        "jinja2>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-asyncio>=0.15.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=0.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "kari-ext=core.extensions.sdk.cli:cli",
            "kari-ext-launch=core.extensions.launch.cli:launch_cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Code Generators",
    ],
    python_requires=">=3.8",
    keywords="kari ai extensions sdk development",
    project_urls={
        "Documentation": "https://docs.kari.ai/extensions",
        "Source": "https://github.com/kari-ai/extensions-sdk",
        "Tracker": "https://github.com/kari-ai/extensions-sdk/issues",
        "Community": "https://discord.gg/kari-extensions",
    },
)