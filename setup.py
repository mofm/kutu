from setuptools import setup, find_packages


classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Intended Audience :: Information Technology",
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.8",
    "Topic :: System :: Systems Administration",
    "Topic :: Terminals",
    "Topic :: Utilities"
]


setup(
    name='kutu',
    packages=find_packages(where='src'),
    packages_dir={"": "src"},
    url='https://github.com/mofm/kutu',
    license='GPLv3',
    author='Emre Eryilmaz',
    author_email='emre.eryilmaz@piesso.com',
    description='kutu, lightweight containerization application',
    scripts=['scripts/ktctl'],
    classifiers=classifiers,
    keywords='container, containerization, container-engine',
    python_requires='>=3.8',

)
