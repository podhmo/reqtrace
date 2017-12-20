PKG = pipenv
PKG = pyramid

search:
	python -m reqtrace --with-uid --logging=DEBUG pip search $(PKG)

download:
	python -m reqtrace --with-uid --logging=DEBUG pip download $(PKG) --dest data
clean:
	rm -f *.whl *.json *.pickle *.tar.gz
	rm -f **/**/*.whl **/**/*.json **/**/*.pickle **/**/*.tar.gz
	rmdir --ignore-fail-on-non-empty roundtrips/*

