# setup.py

import os
import re

import setuptools


# Function to read the version from __init__.py
def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, "__init__.py")).read()
    # Adjust the regex based on how __version__ is defined in your __init__.py
    match = re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py)
    if match:
        return match.group(1)
    else:
        raise RuntimeError(f"Unable to find version string in {package}/__init__.py.")


# Function to read the long description from README.md
def get_long_description(readme_file="README.md"):
    """
    Return the long description from the README file.
    """
    try:
        with open(readme_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: '{readme_file}' not found. Long description will be empty.")
        return None


# Package name (as used in import statements)
PACKAGE_NAME = "jrag"
# Version read from the package's __init__.py
VERSION = get_version(PACKAGE_NAME)
# Long description read from README.md
LONG_DESCRIPTION = get_long_description()

# Define development dependencies
DEV_DEPENDENCIES = [
    "pytest",
    "pytest-cov",
    "pylint",
    "black",
    "isort",
    "build",
    "twine",
    "pre-commit",
]

setuptools.setup(
    name=PACKAGE_NAME,
    version=VERSION,
    author="Cormac Rynne",
    description=(
        "A Python package to convert JSON/dictionaries to flattened strings for RAG systems, "
        "with optional jsonpath_ng configuration."
    ),
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",  # Type of the long description file
    url="https://github.com/cormac-rynne/jrag",  # Optional: Replace with your repo URL
    # Automatically find packages in the current directory
    packages=setuptools.find_packages(exclude=["tests*", "examples*"]),
    # Core runtime dependencies
    install_requires=[
        "jsonpath-ng",
    ],
    # Optional dependencies (e.g., for development)
    extras_require={
        "dev": DEV_DEPENDENCIES,
    },
    # Minimum Python version required
    python_requires=">=3.7",
    # PyPI classifiers to categorize the project
    # Full list: https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 4 - Beta",  # Or "3 - Alpha", "5 - Production/Stable"
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",  # Choose your license
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing",
        "Topic :: Utilities",
    ],
    # Optional keywords for PyPI search
    keywords="json, flatten, rag, string, converter, jsonpath, text processing",
    # If your package needs data files included, uncomment and modify:
    # include_package_data=True,
    # package_data={
    #     'your_package': ['data/*.json'],
    # },
    # If your package has script entry points, uncomment and modify:
    # entry_points={
    #     'console_scripts': [
    #         'my-script=your_package.module:main_function',
    #     ],
    # },
)
