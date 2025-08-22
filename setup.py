import setuptools
import os

# Read the contents of your README file.
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="reporthanter",  
    version="0.2.0",
    author="Andreas Sjödin",
    author_email="andreas.sjodin@gmail.com",
    description="An interactive HTML report generator for sequence classification analyses.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/druvus/reporthanter",  
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        "pandas>=1.5",
        "numpy>=1.21",
        "altair>=4.2",
        "panel>=0.14",
        "pyfastx>=0.22",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=22.0",
            "flake8>=5.0",
            "mypy>=1.0",
            "pre-commit>=2.20",
        ],
        "docs": [
            "sphinx>=5.0",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "reporthanter=reporthanter.panel_report_cli:main",
        ],
    },
    include_package_data=True,
)
