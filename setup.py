import setuptools

exec(open("epd_dashboard/_version.py", "r").read())

with open("README.md", "r") as fh:
    long_description = fh.read()

package_data = {
"": [
    "assets/*",
    "assets/fonts/*",
    "apps.json"
    ]
}

setuptools.setup(
    name="epd_dashboard",
    version=__version__,
    author="Gabriella Morgan",
    author_email="gabriellarosemorgan@proton.me",
    description="Application launcher for the Raspberry Pi with Waveshare 2.13in Touch E-Paper Display",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gabbymorgan/epd-dashboard",
    packages=setuptools.find_packages(),
    package_data=package_data,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points= {
        'console_scripts': ['epd_dashboard=epd_dashboard.app:main']
    },
    install_requires=["gpiozero", "smbus", "spidev", "lgpio", "numpy", "pillow", "arrow", "readchar"],
    python_requires=">=3.7",
)
