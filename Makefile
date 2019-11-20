unit-test:
	py.test --ignore=tests/api/integration/ -v -s -x --cov-report term-missing --cov=app tests

runserver:
	exec gunicorn 'app.application:get_or_create()' --config 'app/config/gunicorn.conf'
