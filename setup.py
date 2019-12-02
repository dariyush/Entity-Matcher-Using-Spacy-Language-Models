import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "NLP",
    version = "2019.03.29",
    author = "Ali Moh",
    author_email = "mohammadi.aliakbar@gmail.com",
    description = "NLP for XXX",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url="https://www.xxxxxxx.com",
    packages = setuptools.find_packages(),
    install_requires = ['spacy','pyodbc','sklearn','pandas'],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
