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
        "fastapi[all]",
        "langchain",
        "langchain_openai",
        "sentence-transformers",
        "uvicorn",
        "pydantic",
        "scikit-learn",
        "networkx",
        "matplotlib",
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

# 添加自动安装我们新引入的依赖项（AI 模块与网关模块）
# 这将在这个旧 setup.py 原有的基础上 append。稍后我们将完整重写它。
