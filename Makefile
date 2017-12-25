test:
	DEBUG=1 python setup.py test

setup:
	pip install -e .[googleapi]
