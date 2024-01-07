from setuptools import find_packages, setup

setup(
    name="newsie",
    packages=find_packages(exclude=["newsie_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud",
        "dagster-duckdb-pandas",
        "dagster-slack",
        "langchain",
        "-U lanchain-community",
        "openai",
        "feedparser",
        "beautifulsoup4",
        "pandas"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
