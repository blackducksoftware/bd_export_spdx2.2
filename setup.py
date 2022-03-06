import setuptools
import platform

platform_system = platform.system()

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bd_export_spdx2.2",
    version="0.23",
    author="Matthew Brady",
    author_email="w3matt@gmail.com",
    description="Export an SPDX version 2.2 JSON file from a Black Duck project.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/matthewb66/bd_export_spdx2.2",
    packages=setuptools.find_packages(),
    install_requires=['blackduck>=1.0.0',
                      'lxml',
                      'aiohttp'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache-2.0",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.0',
    entry_points={
        'console_scripts': ['bd_export_spdx=export_spdx.main:run'],
    },
)
