#!/usr/bin/env python3
"""PDF to HWP Converter - 설치 스크립트"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [
        line.strip()
        for line in f
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="pdf-to-hwp",
    version="1.0.0",
    author="Jingyeskan",
    description="PDF 파일을 이미지화하여 HWP로 변환하는 에이전트",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eunseok7979/Jingyeskan-1.0",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Office Suites",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pdf-to-hwp=main:main",
            "pdf-integrator=pdf_integrator:main",
        ],
    },
)
