
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="os-backup-cli",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive backup solution for Ubuntu VPS servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/os-backup",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Archiving :: Backup",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "click>=8.0.0",
        "paramiko>=2.7.2",
        "cryptography>=3.4.8",
        "google-auth>=2.0.0",
        "google-auth-oauthlib>=0.4.0",
        "google-auth-httplib2>=0.1.0",
        "google-api-python-client>=2.0.0",
        "python-dotenv>=0.19.0",
        "tabulate>=0.8.9",
    ],
    entry_points={
        "console_scripts": [
            "osbackup=cli:cli",
        ],
    },
)
