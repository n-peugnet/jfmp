from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="jfmp",
    version="0.1.0b1",
    author="Nicolas Peugnet",
    author_email="n.peugnet@free.fr",
    description="A minimalist cross-platform gapless music player for Jellyfin",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/n-peugnet/jfmp",
    packages=['jfmp'],
    entry_points={
        "gui_scripts": [
            "jfmp = jfmp.app:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "jellyfin-apiclient-python>=1.2,<2",
        "musicplayer @ git+https://github.com/n-peugnet/music-player-core.git@test-branch",
        "appdirs>=1,<2",
        "pyside2>=5,<6",
    ]
)
