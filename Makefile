PORT ?= 5080
TEST ?=.
BLACK_CONFIG ?= --exclude=venv --skip-string-normalization --line-length 100
CHECK ?= --check

unit-test:
	TESTING=1 py.test --ignore=tests/api/integration/ -v -s -x --cov-report term-missing --cov=app tests --junitxml=test-results/report.xml

integration-test:
	TESTING=1 py.test tests/api/integration/ -v -s -x --cov-report term-missing --cov=app tests --junitxml=test-results/report.xml

runserver:
	exec gunicorn 'app.application:get_or_create()' --config 'app/config/gunicorn.conf'


.PHONY: run_dev_server
run_dev_server:
	FLASK_DEBUG=1 FLASK_APP='app.application:get_or_create()' flask run --host 0.0.0.0 --port ${PORT}

.PHONY: run_tests
run_tests: integration-test

check: flake8 black

format: CHECK=
format: black

black:
	black ${BLACK_CONFIG} ${CHECK} .

flake8:
	flake8 .
