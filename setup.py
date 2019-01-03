# coding=utf-8
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pap_logger",
    version="0.0.1",
    author="KurisuD",
    author_email="author@example.com",
    description="A 'prêt-à-porter' logger",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KurisuD/pap_logger",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Logging"
    ],
)