# file: setup.py

from setuptools import setup, find_packages

setup(
    name="promptrecon",
    version="0.3.0",
    packages=find_packages(),
    # 核心依赖
    install_requires=[
        "rich",
        "gitpython",
    ],
    # v0.3: 将 cli.py:main 注册为命令行工具
    entry_points={
        "console_scripts": [
            # 当你 pip install . 
            # 这会创建一个叫 "promptrecon" 的可执行命令
            "promptrecon = promptrecon.cli:main"
        ]
    },
    author="[Your Name/Handle Here]",
    description="A multithreaded scanner for hardcoded AI System Prompts.",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Security",
        "Topic :: Utilities",
    ],
)
