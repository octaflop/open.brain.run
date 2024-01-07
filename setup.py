from setuptools import find_packages, setup

setup(
    name="newsie",
    packages=find_packages(exclude=["newsie_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
