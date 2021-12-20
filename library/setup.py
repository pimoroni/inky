#!/usr/bin/env python3

"""
Copyright (c) 2017 Pimoroni.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from setuptools import setup

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Operating System :: POSIX :: Linux',
    'License :: OSI Approved :: MIT License',
    'Intended Audience :: Developers',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Topic :: Software Development',
    'Topic :: System :: Hardware'
]

setup(
    name='inky',
    version='1.3.0',
    author='Philip Howard',
    author_email='phil@pimoroni.com',
    description='Inky pHAT Driver',
    long_description=open('README.md').read() + '\n' + open('CHANGELOG.txt').read(),
    long_description_content_type="text/markdown",
    license='MIT',
    keywords='Raspberry Pi e-paper display driver',
    url='http://www.pimoroni.com',
    project_urls={'GitHub': 'https://www.github.com/pimoroni/inky'},
    classifiers=classifiers,
    py_modules=[],
    packages=['inky'],
    include_package_data=True,
    install_requires=['numpy', 'smbus2', 'spidev'],
    extras_require={
        'rpi-gpio-output': ['RPi.GPIO'],
        'rpi': ['RPi.GPIO'],
        'example-depends': ['requests', 'geocoder', 'beautifulsoup4', 'font-fredoka-one', 'font-source-serif-pro', 'font-hanken-grotesk', 'font-intuitive']
    }
)
