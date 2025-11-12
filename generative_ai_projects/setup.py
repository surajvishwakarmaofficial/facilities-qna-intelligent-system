####### setup.py ##############
from setuptools import setup, find_packages

setup(
    name="yash-facilities-ai",
    version="1.0.0",
    description="YASH Facilities Management AI Assistant",
    author="Your Name",
    author_email="your.email@yash.com",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "langchain==0.1.0",
        "litellm==1.17.0",
        "pymilvus==2.3.4",
        "redis==5.0.1",
        "sqlalchemy==2.0.23",
        "sentence-transformers==2.2.2",
        "pydantic==2.4.2",
        "python-dotenv==1.0.0",
    ],
    python_requires=">=3.9",
)