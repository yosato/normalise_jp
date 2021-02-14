import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="normalise_jp", # Replace with your own username
    version="0.0.1",
    author="Yo Sato",
    author_email="yosato16@gmail.com",
    description="jp normalisation package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yosato/normalise_jp.git",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
)
