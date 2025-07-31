from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="esg-reporter",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Multi-Agent AI Research System for ESG Analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ESGreporter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial Services",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "esg-reporter=streamlit_app:main",
        ],
    },
    keywords="esg, ai, agents, research, finance, sustainability, langgraph",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/ESGreporter/issues",
        "Source": "https://github.com/yourusername/ESGreporter",
        "Documentation": "https://github.com/yourusername/ESGreporter/blob/main/README.md",
    },
)
