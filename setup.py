import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dpy-utils",
    version="0.0.1",
    author="Clari",
    author_email="clarinet.puppy@gmail.com",
    description="Some discord.py utils by Clari",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Clari-7744/dpy-utils",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"ContextEditor": "ContextEditor", "converters": "converters", "duration": "duration", "tasks": "tasks"},
    packages=["ContextEditor", "converters", "duration", "tasks"].
    python_requires=">=3.6",
)
