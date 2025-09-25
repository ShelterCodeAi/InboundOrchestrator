#!/usr/bin/env python3
"""
Setup script for InboundOrchestrator.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    requirements = [
        line.strip() 
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
else:
    requirements = [
        "rule-engine>=4.5.0",
        "boto3>=1.34.0",
        "pyyaml>=6.0",
        "email-validator>=2.1.0",
        "python-dotenv>=1.0.0",
        "dataclasses-json>=0.6.0"
    ]

setup(
    name="inbound-orchestrator",
    version="0.1.0",
    author="ShelterCodeAi",
    author_email="contact@sheltercode.ai",
    description="A Python rules engine for processing emails and routing to SQS queues",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ShelterCodeAi/InboundOrchestrator",
    packages=find_packages(),
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
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Email",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "inbound-orchestrator=inbound_orchestrator.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "inbound_orchestrator": [
            "config/*.yaml",
            "config/*.json",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/ShelterCodeAi/InboundOrchestrator/issues",
        "Source": "https://github.com/ShelterCodeAi/InboundOrchestrator",
        "Documentation": "https://github.com/ShelterCodeAi/InboundOrchestrator/blob/main/README.md",
    },
    keywords="email processing rules engine sqs aws automation workflow",
)