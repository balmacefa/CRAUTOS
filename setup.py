from setuptools import setup, find_packages

setup(
    name="crautos-analyzer",
    version="1.0.0",
    description="CRAutos Market Intelligence System",
    author="Sebas10CR",
    author_email="",
    url="https://github.com/Sebas10CR/CRAUTOS",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "sqlalchemy>=2.0.23",
        "psycopg2-binary>=2.9.9",
        "selenium>=4.15.2",
        "beautifulsoup4>=4.12.2",
        "pandas>=2.1.3",
        "redis>=5.0.1",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
    ],
)