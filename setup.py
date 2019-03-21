import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, "README.rst")) as f:
        README = f.read()
    with open(os.path.join(here, "CHANGES.txt")) as f:
        CHANGES = f.read()
except IOError:
    README = CHANGES = ""

install_requires = ["requests", "httplib2", "magicalimport"]

googleapi_extras = ["google-api-python-client"]

docs_extras = []

tests_require = []

testing_extras = tests_require + []

setup(
    name="reqtrace",
    version="0.0.0",
    description="tracing request. (don't use this in production)",
    long_description=README + "\n\n" + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    keywords="requests, httplib2, urllib",
    author="podhmo",
    author_email="ababjam61@gmail.com",
    url="https://github.com/podhmo/reqtrace",
    packages=find_packages(exclude=["reqtrace.tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        "testing": testing_extras,
        "docs": docs_extras,
        "googleapi": googleapi_extras,
    },
    tests_require=tests_require,
    test_suite="reqtrace.tests",
    entry_points="""
    [console_scripts]
    py-reqtrace=reqtrace.commands.reqtrace:main
""",
)
