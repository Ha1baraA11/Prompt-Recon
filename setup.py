# file: setup.py

from setuptools import setup, find_packages

setup(
    name="promptrecon",
    version="0.4.0",
    packages=find_packages(),
    install_requires=[
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "promptrecon = promptrecon.cli:main"
        ]
    },
    author="Ha1baraA11",
    description="Local code secrets scanner with Git pre-commit hook.",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Security",
        "Topic :: Utilities",
    ],
)
