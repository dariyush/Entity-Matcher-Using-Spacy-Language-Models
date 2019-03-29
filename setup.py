import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "AMENLP",
    version = "2019.03.29",
    author = "Ali Moh",
    author_email = "a.mohammadi@amegroup.com",
    description = "NLP for AME",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url="https://www.amegroup.com",
    packages = setuptools.find_packages(),
    install_requires = ['spacy','pyodbc','sklearn','pandas'],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)