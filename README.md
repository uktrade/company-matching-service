# Company Matching Service Platform Migration

This temporary branch is intended to provide an easy way to check the service running on Gov PaaS against the migrated version running on DBT PaaS.

### Authentication

In order to run the tests we first need to create a HAWK USER on both environments to authenticate with.

On Gov PaaS:

```bash
cf login
cf ssh company-matching-service
/tmp/lifecycle/shell
python3 manage.py dev add_hawk_user --client_id=<abc> --client_key=<123> --client_scope="*" --description=migration-test
```

On DBT PaaS:

```bash
copilot svc exec --app company-matching-service --env prod --name company-matching-service --command "launcher bash"
python manage.py dev add_hawk_user --client_id=<abc> --client_key=<123> --client_scope="*" --description=migration-test
```

These credentials should be removed again once testing has been completed

### Run tests

```bash
HAWK_CLIENT_ID=<abc> HAWK_CLIENT_KEY=<123> pytest test_platform_migration.py
```
