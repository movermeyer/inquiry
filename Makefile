db:
	@psql inquiry -c "drop schema public cascade;create schema public;"
	@psql inquiry -f tests/demo.sql

test:
	. venv/bin/activate; nosetests --rednose --with-cov --cov-config=.coveragerc

upload:
	python setup.py sdist upload
