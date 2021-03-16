.PHONY: build

black-check:
	black --check --diff --target-version=py38 .

black-reformat:
	black --target-version=py38 .

build:
	python setup.py sdist

clean:
	find . -name '*.pyc' | xargs rm
	rm -Rif *.egg-info/
	rm -Rif .cache/
	rm -Rif .tox/
	rm -Rif __pycache__
	rm -Rif build/
	rm -Rif dist/
	rm -Rif prof/

flake_ignore = --ignore=E203,E266,E501,W503
flake_options = --isolated --max-line-length=88

flake8:
	flake8 ${flake_ignore} ${flake_options}

isort-check:
	isort \
	--case-sensitive \
	--check-only \
	--diff \
	--force-grid-wrap=0 \
	--line-width=88 \
	--multi-line=3 \
	--project=abjad \
	--thirdparty=uqbar \
	--trailing-comma \
	--use-parentheses \
	.

isort-reformat:
	isort \
	--case-sensitive \
	--force-grid-wrap=0 \
	--line-width=88 \
	--multi-line=3 \
	--project=abjad \
	--thirdparty=uqbar \
	--trailing-comma \
	--use-parentheses \
	.

mypy:
	mypy .

pytest:
	pytest .

pytest-x:
	pytest -x .

reformat:
	make black-reformat
	make isort-reformat

release:
	make clean
	make build
	pip install -U twine
	twine upload dist/*.tar.gz

check:
	make black-check
	make flake8
	make isort-check
	make mypy

test:
	make check
	make pytest
