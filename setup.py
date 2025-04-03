from setuptools import setup, find_packages

setup(
    name="robinhood_ai_trading_bot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'openai',
        'python-dotenv',
        'requests'
    ],
    python_requires='>=3.8',
)