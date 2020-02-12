from datetime import datetime, timedelta

from app.algorithm import Matcher

"""

Company description short format used in tests:
(datetime, companies_house_id, duns_number, company_name, contact_email, cdms_ref, postcode)

Shorter tuple will assume None values for the remaining attributes.

If datetime is labeled 'inc' each description will be assigned an incremental timestamp increasing 
from low to high indices.

Expected matches format used in tests:
(id, match_id, similarity)

"""


def test_matcher_1(app_with_db):
    """
        Test matching with no conflicting data
    """
    _assert_matches(
        descriptions=[('inc', 1, 'a', 'k'), ('inc', 2, 'b', 'l'), ('inc', 3, 'c', 'm')],
        expected_matches=[('1', 1, '111000'), ('2', 2, '111000'), ('3', 3, '111000')]
    )


def test_matcher_2(app_with_db):
    """
        Test matching with conflicting data:
            most recent description with id '3' links same duns/name to new chid

    """
    _assert_matches(
        descriptions=[('inc', 1, 'a', 'k'), ('inc', None, 'a', 'l'), ('inc', 2, 'a', 'k')],
        expected_matches=[('1', 1, '100000'), ('2', 2, '011000'), ('3', 2, '111000')]
    )


def test_matcher_3(app_with_db):
    """
        Test matching with conflicting data:
            most recent description should get priority
    """
    _assert_matches(
        descriptions=[('2019-01-02 00:00:00', 1, 'a', 'k')],
        expected_matches=[('1', 1, '111000')],
    )
    # the previous more recent description states that 'a' and 'k' are not part of this group
    _assert_matches(
        descriptions=[('2019-01-01 00:00:00', 2, 'a', 'k')],
        expected_matches=[('1', 2, '100000')],
    )


def test_matcher_4(app_with_db):
    """
        Test matching with conflicting data:
            1:['x', 'y', None] -> 2:[None, 'y', None] => 2 should have same group as 1
    """
    _assert_matches(
        descriptions=[('inc', 1, 'a', None), ('inc', None, 'a', None)],
        expected_matches=[('1', 1, '110000'), ('2', 1, '010000')]
    )


def test_matcher_5a_batch(app_with_db):
    """
        Test matching with conflicting data:
            batch mapping should give same match_ids but can have different similarity strings

    """
    _assert_matches(
        descriptions=[('inc', 1, 'a', 'k'), ('inc', 1, 'b', None), ('inc', 2, 'b', None),
                      ('inc', None, 'b', 'l'), ('inc', None, 'c', 'k')],
        expected_matches=[
            ('1', 1, '110000'), ('2', 1, '100000'), ('3', 2, '110000'), ('4', 2, '011000'), ('5', 3, '011000')
        ]
    )


def test_matcher_5b_row(app_with_db):
    """
        Test matching with conflicting data:
            batch mapping should give same match_ids but can have different similarity strings

    """
    _assert_matches(
        descriptions=[('2019-01-01 00:00:00', 1, 'a', 'k')],
        expected_matches=[('1', 1, '111000')]
    )
    _assert_matches(
        descriptions=[('2019-01-02 00:00:00', 1, 'b', None)],
        expected_matches=[('1', 1, '110000')]
    )
    _assert_matches(
        descriptions=[('2019-01-03 00:00:00', 2, 'b', None)],
        expected_matches=[('1', 2, '110000')]
    )
    _assert_matches(
        descriptions=[('2019-01-04 00:00:00', None, 'b', 'l')],
        expected_matches=[('1', 2, '011000')]
    )
    _assert_matches(
        descriptions=[('2019-01-05 00:00:00', None, 'c', 'k')],
        expected_matches=[('1', 3, '011000')]
    )


def test_matcher_6(app_with_db):
    """
        Test matching with uncleaned cmds_ref
    """
    _assert_matches(
        descriptions=[
            ('inc', None, None, None, None, 'ORG-10052267'), ('inc', None, None, None, None, '10052267')
        ],
        expected_matches=[('1', 1, '000010'), ('2', 1, '000010')]
    )


def test_matcher_7(app_with_db):
    """
        Test matching with contact email domain
    """
    _assert_matches(
        descriptions=[
            ('inc', None, None, None, 'john@domain.com', None),
            ('inc', None, None, None, 'ann@domain.com', None),
            ('inc', None, None, None, 'ann@otherdomain.com', None)
        ],
        expected_matches=[('1', 1, '000100'), ('2', 1, '000100'), ('3', 2, '000100')]
    )


def _assert_matches(descriptions, expected_matches):
    matcher = Matcher()
    json_data = _create_json(descriptions)
    matches = matcher.match(json_data)
    assert matches == expected_matches


def _create_json(value_list):
    json_data = []
    timestamp = datetime.strptime('2019-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    for i, values in enumerate(value_list):
        data = {
            'id': str(i + 1),
            'source': 'dit.datahub',
        }
        if values[0] == 'inc':
            data['datetime'] = (timestamp + timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S")
        else:
            data['datetime'] = values[0]
        if values[0]:
            data['companies_house_id'] = values[1]
        if len(values) > 2 and values[2]:
            data['duns_number'] = values[2]
        if len(values) > 3 and values[3]:
            data['company_name'] = values[3]
        if len(values) > 4 and values[4]:
            data['contact_email'] = values[4]
        if len(values) > 5 and values[5]:
            data['cdms_ref'] = values[5]
        if len(values) > 6 and values[6]:
            data['postcode'] = values[6]
        json_data.append(data)
    return json_data


