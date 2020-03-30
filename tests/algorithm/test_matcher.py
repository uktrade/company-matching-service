from datetime import datetime, timedelta

import pytest

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


@pytest.mark.parametrize(
    'descriptions,expected_matches,update,match,dnb_match',
    (
        #   Test matching with no conflicting data
        (
            [
                ('inc', 'ch1', 'dun1', 'name1'),
                ('inc', 'ch2', 'dun2', 'name2'),
                ('inc', 'ch3', 'dun3', 'name3'),
            ],
            [('1', 1, '111000'), ('2', 2, '111000'), ('3', 3, '111000')],
            True,
            True,
            False,
        ),
        #   Test matching with conflicting data:
        #       most recent description with id '3' links same duns/name to new chid
        (
            [
                ('inc', 'ch1', 'dun1', 'name1'),
                ('inc', None, 'dun1', 'name2'),
                ('inc', 'ch2', 'dun1', 'name1'),
            ],
            [('1', 1, '100000'), ('2', 2, '011000'), ('3', 2, '111000')],
            True,
            True,
            False,
        ),
        #   Test batch matching with missing data
        (
            [('inc', 'ch1', 'dun1', None), ('inc', None, 'dun1', None)],
            [('1', 1, '110000'), ('2', 1, '010000')],  # should be same group
            True,
            True,
            False,
        ),
        #   Test matching with invalid companies_house id
        (
            [('inc', 'NotRegis'), ('inc', 'not reg'), ('inc', 'n/a'), ('inc', 'N/A'), ('inc', '')],
            [
                ('1', None, '000000'),
                ('2', None, '000000'),
                ('3', None, '000000'),
                ('4', None, '000000'),
                ('5', None, '000000'),
            ],
            True,
            True,
            False,
        ),
        #   Test matching with uncleaned cdms_ref
        (
            [
                ('inc', None, None, None, None, 'ORG-10052267'),
                ('inc', None, None, None, None, '10052267'),
            ],
            [('1', 1, '000010'), ('2', 1, '000010')],
            True,
            True,
            False,
        ),
        #   Test matching with contact email domain
        (
            [
                ('inc', None, None, None, 'john@domain.com', None),
                ('inc', None, None, None, 'ann@domain.com', None),
                ('inc', None, None, None, 'ann@otherdomain.com', None),
            ],
            [('1', 1, '000100'), ('2', 1, '000100'), ('3', 2, '000100')],
            True,
            True,
            False,
        ),
        #   Test matching with similar company names
        (
            [
                ('inc', None, None, 'corp ltd', None, None),
                ('inc', None, None, 'corp limited', None, None),
                ('inc', None, None, 'test ltd', None, None),
            ],
            [('1', 1, '001000'), ('2', 1, '001000'), ('3', 2, '001000')],
            True,
            True,
            False,
        ),
        #   Test dnb matching with no conflicting data
        (
            [('inc', 'ch1', 'dun1', 'name1'), ('inc', 'ch2', None, 'name2')],
            [('1', 'dun1', '111000'), ('2', None, '101000')],
            True,
            True,
            True,
        ),
        #   Test dnb matching with multiple dnb numbers in match group:
        #       if dun_number present in desc select that one
        #       else the most recent one is selected
        (
            [
                ('inc', 'ch1', 'dun1a', 'name1'),
                ('inc', 'ch1', 'dun1b', 'name1'),
                ('inc', 'ch1', None, 'name1'),
            ],
            [
                ('1', 'dun1a', '111000'),  # select current
                ('2', 'dun1b', '111000'),  # select current
                ('3', 'dun1b', '101000'),  # select most recent
            ],
            True,
            True,
            True,
        ),
    ),
)
def test_matcher(descriptions, expected_matches, update, match, dnb_match, app_with_db):
    _assert_matches(descriptions, expected_matches, update, match, dnb_match)


def test_matcher_timestamp_priority(app_with_db):
    """
        Test matching with conflicting data:
            most recent description should get priority
    """
    _assert_matches(
        descriptions=[('2019-01-02 00:00:00', 'ch1', 'dun1', 'name1')],
        expected_matches=[('1', 1, '111000')],
    )
    # the previous more recent description states that 'dun1' and 'name1' are not part of this group
    _assert_matches(
        descriptions=[('2019-01-01 00:00:00', 'ch2', 'dun1', 'name1')],
        expected_matches=[('1', 2, '100000')],
    )
    # 'dun1' and 'name1' should still belong to group 1
    _assert_matches(
        descriptions=[('2019-01-03 00:00:00', None, 'dun1', 'name1')],
        expected_matches=[('1', 1, '011000')],
        update=False,
    )


def test_matcher_missing_data(app_with_db):
    """
        Test matching with missing data:
            'dun1' should be regrouped when older or newer
            missing information is provided
    """
    _assert_matches(
        descriptions=[('2019-01-03 00:00:00', None, 'dun1', None)],
        expected_matches=[('1', 1, '010000')],
    )
    _assert_matches(
        descriptions=[('2019-01-02 00:00:00', 'ch1', 'dun1', None)],
        expected_matches=[('1', 2, '110000')],
    )
    _assert_matches(
        descriptions=[('2019-01-05 00:00:00', None, 'dun1', None)],
        expected_matches=[('1', 2, '010000')],
        update=False,
    )  # dun1 should be reassigned to group 2
    _assert_matches(
        descriptions=[('2019-01-04 00:00:00', None, 'dun1', 'name1')],
        expected_matches=[('1', 2, '011000')],
    )
    _assert_matches(
        descriptions=[('2019-01-05 00:00:00', 'ch1', 'dun1', 'name1')],
        expected_matches=[('1', 2, '111000')],
        update=False,
    )  # all fields should be part of group 2


def test_matcher_existing_dependencies(app_with_db):
    """
        Test priority field changes group:
            existing dependency 'name1' on 'dun1' should be updated
            when priority node 'dun1' gets regrouped
    """
    _assert_matches(
        descriptions=[('2019-01-01 00:00:00', None, 'dun1', 'name1')],
        expected_matches=[('1', 1, '011000')],
    )
    _assert_matches(
        descriptions=[('2019-01-02 00:00:00', 'ch1', 'dun1', None)],
        expected_matches=[('1', 2, '110000')],
    )
    _assert_matches(
        descriptions=[('2019-01-03 00:00:00', None, None, 'name1')],
        expected_matches=[('1', 2, '001000')],
        update=False,
    )


def test_matcher_existing_dependencies_with_gap(app_with_db):
    """
        Test priority field with gap changes group:
            'test@email1' should be regrouped when priority node 'dun1'
            gets regrouped
    """
    _assert_matches(
        descriptions=[('2019-01-01 00:00:00', None, 'dun1', None, 'test@email1')],
        expected_matches=[('1', 1, '010100')],
    )
    _assert_matches(
        descriptions=[('2019-01-02 00:00:00', 'ch1', 'dun1', None)],
        expected_matches=[('1', 2, '110000')],
    )
    _assert_matches(
        descriptions=[('2019-01-03 00:00:00', None, None, 'name1', 'test@email1')],
        expected_matches=[('1', 2, '000100')],
        update=False,
    )


def test_matcher_field_priority_regroup(app_with_db):
    """
        Test field priority matching:
            'name1' should be regrouped with priority node 'ch2'
            because companies_house_id has higher priority then duns_number
    """
    _assert_matches(
        descriptions=[('2019-01-01 00:00:00', None, 'dun1', 'name1')],
        expected_matches=[('1', 1, '011000')],
    )  # dun1, name1:1 -> dun1:1, name1:3
    _assert_matches(
        descriptions=[('2019-01-02 00:00:00', 'ch2', None, 'name1')],
        expected_matches=[('1', 2, '101000')],
    )  # ch2, name1:3
    _assert_matches(
        descriptions=[('2019-01-03 00:00:00', 'ch2', 'dun1', 'name1')],
        expected_matches=[('1', 2, '101000')],
        update=False,
    )  # name1 part of group 2


def test_matcher_field_priority_no_regroup(app_with_db):
    """
        Test field priority matching:
            'name1' should not be regrouped with priority node 'dun2'
            because higher priority node has preference when data missing
    """
    _assert_matches(
        descriptions=[('2019-01-01 00:00:00', 'ch1', 'dun1', 'name1')],
        expected_matches=[('1', 1, '111000')],
    )  # ch1, dun1, name1:1
    _assert_matches(
        descriptions=[('2019-01-02 00:00:00', None, 'dun2', 'name1')],
        expected_matches=[('1', 2, '010000')],
    )  # dun2:2, name1:1
    _assert_matches(
        descriptions=[('2019-01-03 00:00:00', 'ch1', 'dun1', 'name1')],
        expected_matches=[('1', 1, '111000')],
        update=False,
    )  # name1 not part of group


def test_batch_matcher_batch_vs_sequential(app_with_db):
    """
        Test batch matching should give same match_ids as sequential matching
        but can have different similarity strings
    """
    _assert_matches(
        descriptions=[
            ('inc', 'ch1', 'dun1', 'name1'),  # ch1, dun1, name1: 1
            ('inc', 'ch1', 'dun2', None),  # ch1, dun2: 1 -> ch1:1, dun2:2
            ('inc', 'ch2', 'dun2', None),  # ch2, dun2: 2
            ('inc', None, 'dun2', 'name2'),  # dun2: 2, name2:2
            ('inc', None, 'dun3', 'name1'),  # dun3: 3, name1:1 (priority node pref on missing data)
        ],
        expected_matches=[
            ('1', 1, '111000'),
            ('2', 1, '100000'),
            ('3', 2, '110000'),
            ('4', 2, '011000'),
            ('5', 3, '010000'),
        ],
    )


def test_sequential_matcher_batch_vs_sequential(app_with_db):
    """
        Test batch matching should give same match_ids as sequential matching
        but can have different similarity strings

    """
    _assert_matches(
        descriptions=[('2019-01-01 00:00:00', 'ch1', 'dun1', 'name1')],
        expected_matches=[('1', 1, '111000')],
    )
    _assert_matches(
        descriptions=[('2019-01-02 00:00:00', 'ch1', 'dun2', None)],
        expected_matches=[('1', 1, '110000')],
    )  # different similarity string because next description not available yet
    _assert_matches(
        descriptions=[('2019-01-03 00:00:00', 'ch2', 'dun2', None)],
        expected_matches=[('1', 2, '110000')],
    )
    _assert_matches(
        descriptions=[('2019-01-04 00:00:00', None, 'dun2', 'name2')],
        expected_matches=[('1', 2, '011000')],
    )
    _assert_matches(
        descriptions=[('2019-01-05 00:00:00', None, 'dun3', 'name1')],
        expected_matches=[('1', 3, '010000')],
    )


def _assert_matches(descriptions, expected_matches, update=True, match=True, dnb_match=False):
    matcher = Matcher()
    json_data = _create_json(descriptions)
    matches = matcher.match(json_data, update, match, dnb_match)

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
