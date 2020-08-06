import pytest


@pytest.fixture(scope='module')
def add_mapping_db(app_with_db_module):
    def _method(mappings, model):
        for mapping in mappings:
            field = [
                key
                for key in mapping.keys()
                if key not in ['prev_match_id', 'match_id', 'id', 'source', 'datetime']
            ][0]
            defaults = {
                'prev_match_id': mapping.get('prev_match_id', None),
                'match_id': mapping.get('match_id', None),
                'source': mapping.get('prev_match_id', None),
                'datetime': mapping.get('datetime', None),
            }
            model.get_or_create(**{field: mapping.get(field, None)}, defaults=defaults)

    return _method
