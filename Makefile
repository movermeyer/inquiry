db:
	@psql inquiry -c "drop schema public cascade;create schema public;"
	@psql inquiry -f tests/demo.sql
