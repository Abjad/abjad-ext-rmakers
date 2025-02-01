#! /usr/bin/env python
import pathlib

import setuptools

name = "rmakers"


def read_version():
    root_path = pathlib.Path(__file__).parent
    version_path = root_path / "abjadext" / name / "_version.py"
    with version_path.open() as file_pointer:
        file_contents = file_pointer.read()
    local_dict = {}
    exec(file_contents, None, local_dict)
    return local_dict["__version__"]


if __name__ == "__main__":
    setuptools.setup(
        author="Trevor Bača",
        author_email="trevor.baca@gmail.com",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "License :: OSI Approved :: GNU General Public License (GPL)",
            "Programming Language :: Python :: 3.12",
            "Programming Language :: Python :: 3.13",
            "Topic :: Artistic Software",
        ],
        description="rmakers extends Abjad with tools for rhythm construction.",
        include_package_data=True,
        install_requires=["abjad>=3.21"],
        license="MIT",
        long_description=pathlib.Path("README.md").read_text(),
        keywords="lilypond, music composition, music notation",
        name=f"abjad-ext-{name}",
        packages=["abjadext"],
        platforms="Any",
        python_requires=">=3.12",
        url="http://abjad.github.io",
        version=read_version(),
    )
