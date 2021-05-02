from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dpy-utils",
    version="0.0.1",
    author="Clari",
    author_email="clarinet.puppy@gmail.com",
    url="https://github.com/Clari-7744/dpy-utils",
    license="MIT",
    description="Some discord.py utils by Clari",
    long_description=long_description,
    packages=["context", "converters", "duration", "tasks"],
)
