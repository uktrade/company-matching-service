unit-test:
	py.test --ignore=tests/api/integration/ -v -s -x --cov-report term-missing --cov=app tests --junitxml=test-results/report.xml

integration-test:
	py.test tests/api/integration/ -v -s -x --cov-report term-missing --cov=app tests --junitxml=test-results/report.xml

runserver:
	exec gunicorn 'app.application:get_or_create()' --config 'app/config/gunicorn.conf'
