from setuptools import setup

setup(
    setup_requires=['pbr>=1.9'],
    pbr=True,
    python_requires='>=3.6',
    install_requires=[
        "jellyfin-apiclient-python>=1.2,<2",
        "musicplayer @ git+https://github.com/n-peugnet/music-player-core.git@test-branch",
        "appdirs>=1,<2",
        "pyside2>=5,<6",
    ]
)
