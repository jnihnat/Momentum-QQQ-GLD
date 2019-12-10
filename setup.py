import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Backtrade",
    version="0.0.1",
    author="Jan Ihnat",
    author_email="jnihnat@gmail.com",
    description="Backtrading function",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jnihnat/Momentum-QQQ-GLD",
    entry_points={"console_scripts": ["Backtrade = Backtrade.__main__"]},
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)