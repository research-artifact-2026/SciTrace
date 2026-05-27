from setuptools import setup, find_packages

INSTALL_REQUIRES = [
    "openai>=1.30.0",
    "anthropic>=0.25.0",
    "pydantic>=2.0.0",
    "numpy>=1.26.0",
    "scipy>=1.12.0",
    "matplotlib>=3.8.0",
    "seaborn>=0.13.0",
    "tqdm>=4.66.0",
    "python-dotenv>=1.0.0",
    "pytest>=8.0.0",
    "tiktoken>=0.6.0",
]

setup(
    name="scitrace",
    version="0.1.0",
    description="Trajectory-Aware Safety Reasoning for Scientific Discovery Agents",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=INSTALL_REQUIRES,
    extras_require={
        "vllm": ["torch>=2.2.0", "vllm>=0.4.0", "transformers>=4.40.0", "accelerate>=0.28.0"],
    },
)
