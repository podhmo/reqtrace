PKG = pipenv

search:
	python -m reqtrace --with-uid --logging=DEBUG pip search $(PKG)

download:
	python -m reqtrace --with-uid --logging=DEBUG pip download $(PKG) --dest data

list:
	python -m reqtrace --with-uid --logging=DEBUG pip list --outdated $(PKG)

install-jinja2:
	python -m reqtrace --with-uid --logging=DEBUG pip install --upgrade jinja2
uninstall-jinja2:
	python -m reqtrace --with-uid --logging=DEBUG pip uninstall jinja2

clean:
	rm -f *.whl *.json *.pickle *.tar.gz
	rm -f **/**/*.whl **/**/*.json **/**/*.pickle **/**/*.tar.gz
	rmdir --ignore-fail-on-non-empty roundtrips/*

