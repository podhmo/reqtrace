test:
	DEBUG=1 python setup.py test

setup:
	pip install -e .[googleapi]

build:
#	pip install wheel
	python setup.py bdist_wheel

upload:
#	pip install twine
	twine check dist/reqtrace-$(shell cat VERSION)*
	twine upload dist/reqtrace-$(shell cat VERSION)*

.PHONY: build upload
