from unittest import mock

import pytest

from app.commands.dev import add_hawk_user, db


class TestDevCommand:
    def test_db_cmd_help(self, app_with_db):
        runner = app_with_db.test_cli_runner()
        result = runner.invoke(db)
        assert 'Create/Drop database or database tables' in result.output
        assert result.exit_code == 0
        assert result.exception is None

    def test_add_hawk_cmd_help(self, app_with_db):
        runner = app_with_db.test_cli_runner()
        result = runner.invoke(add_hawk_user)
        assert 'Usage: add_hawk_user [OPTIONS]' in result.output
        assert result.exit_code == 0
        assert result.exception is None

    @pytest.mark.parametrize(
        'client_id,expected_add_user_called', (('client_id', True), (None, False),),
    )
    @mock.patch('app.db.models.HawkUsers.add_user')
    def test_run_hawk_user(self, mock_add_user, client_id, expected_add_user_called, app_with_db):
        mock_add_user.return_value = None
        runner = app_with_db.test_cli_runner()

        args = [
            '--client_key',
            'client_key',
            '--client_scope',
            'client_scope',
            '--description',
            'description',
        ]
        if client_id:
            args.extend(['--client_id', client_id])

        result = runner.invoke(add_hawk_user, args,)
        assert mock_add_user.called is expected_add_user_called
        if not expected_add_user_called:
            assert result.output.startswith('All parameters are required')

    @pytest.mark.parametrize(
        'drop_database,create_tables,drop_tables,' 'create_database,recreate_tables,expected_msg',
        (
            (False, False, False, False, False, True),
            (True, False, False, False, False, False),
            (False, True, False, False, False, False),
            (False, False, True, False, False, False),
            (False, False, False, True, False, False),
            (False, False, False, False, True, False),
        ),
    )
    @mock.patch('flask_sqlalchemy.SQLAlchemy.create_all')
    @mock.patch('flask_sqlalchemy.SQLAlchemy.drop_all')
    @mock.patch('sqlalchemy_utils.create_database')
    @mock.patch('sqlalchemy_utils.drop_database')
    def test_run_db(
        self,
        mock_drop_database,
        mock_create_database,
        mock_drop_tables,
        mock_create,
        drop_database,
        create_tables,
        drop_tables,
        create_database,
        recreate_tables,
        expected_msg,
        app_with_db,
    ):
        mock_drop_database.return_value = None
        mock_create_database.return_value = None
        mock_drop_tables.return_value = None
        mock_create_database.return_value = None
        runner = app_with_db.test_cli_runner()

        args = []
        if drop_tables:
            args.append('--drop_tables')
        if create_tables:
            args.append('--create_tables')
        if drop_database:
            args.append('--drop')
        if create_database:
            args.append('--create')
        if recreate_tables:
            args.append('--recreate_tables')

        result = runner.invoke(db, args)
        assert mock_drop_database.called is drop_database
        assert mock_create_database.called is create_database
        assert mock_drop_tables.called is any([drop_tables, recreate_tables])
        assert mock_create.called is any([create_tables, create_database, recreate_tables])

        if expected_msg:
            assert result.output.startswith('Usage: db [OPTIONS]')
