import json

from app.db import db_utils
from app.db.models import (
    CDMSRefMapping,
    CompaniesHouseIDMapping,
    CompanyNameMapping,
    ContactEmailMapping,
    DunsNumberMapping,
    PostcodeMapping,
)


_ch_name_simplification = """
    lower(coalesce( nullif(
        regexp_replace(
        regexp_replace(
          company_name,
          '^the\s|\s?:\s?|\[|\]|\(|\)|\'\'|\*.*\*|&|,|;|"|ltd\.?$|limited\.?$|\sllp\.?$|\splc\.?$|\sllc\.?$|\sand\s|\sco[\.|\s]|\scompany[\s|$]', ' ', 'gi'),
          '\.|\s', '', 'gi')
      , ''), company_name))
"""  # noqa: W605, W291, E501

_general_name_simplification = f"""
    case when source like 'dit.%%' or source is null then
      lower(coalesce( nullif(
        regexp_replace(
        regexp_replace(
        regexp_replace(
          company_name,
          '^the\s|\s?:\s?|\[|\]|\(|\)|\'\'|\*.*\*|&|,|;|"|ltd\.?$|limited\.?$|\sllp\.?$|\splc\.?$|\sllc\.?$|\sand\s|\sco[\.|\s]|\scompany[\s|$]|\s+', ' ', 'gi'),
          '\s/.*|\s-(\s)?.*|(\s|\.|\(|\_)?duplic.*|\sdupilcat.*|\sdupicat.*|\sdissolved.*|\*?do not .*|((\s|\*)?in)?\sliquidat.*|\sceased trading.*|\strading as.*|t/a.*|\sacquired by.*|\splease\s.*|(do not)?(use)?(.)?(\d{{5}}(\d*)).*|-|\.', '', 'gi'),
          '\.|\s', '', 'gi')
      , ''), company_name))
    else
      {_ch_name_simplification}
    end
"""  # noqa: W605, W291, E501


_field_to_mapping_table = [
    ('companies_house_id', CompaniesHouseIDMapping.__tablename__),
    ('duns_number', DunsNumberMapping.__tablename__),
    ('company_name', CompanyNameMapping.__tablename__),
    ('contact_email', ContactEmailMapping.__tablename__),
    ('cdms_ref', CDMSRefMapping.__tablename__),
    ('postcode', PostcodeMapping.__tablename__),
]


def json_to_tmp_table(json_data):
    stmt = """
        DROP TABLE IF EXISTS tmp;
        CREATE TEMPORARY TABLE tmp (
            id text,
            source text,
            datetime timestamp,
            companies_house_id text,
            duns_number text,
            company_name text,
            contact_email text,
            cdms_ref text,
            postcode text
        );
    """
    db_utils.execute_statement(stmt)
    stmt = f"""
        INSERT INTO tmp (
            id,
            source,
            datetime,
            companies_house_id,
            duns_number,
            company_name,
            contact_email,
            cdms_ref,
            postcode
        )
        SELECT
            id,
            source,
            datetime,
            case when
                lower(companies_house_id) = ANY('{{notregis, not reg,n/a, none, 0, ""}}'::text[])
            then null else lower(companies_house_id) end,
            duns_number,
            {_general_name_simplification},
            lower(split_part(contact_email, '@', 2)),
            regexp_replace(cdms_ref, '\\D','','g'),
            lower(replace(postcode, ' ', ''))
        FROM json_populate_recordset(null::tmp, :data);
    """
    db_utils.execute_statement(stmt, ({"data": json.dumps(json_data)},))


def update_mappings():
    db_utils.execute_statement("SET statement_timeout TO '10h' ")
    to_check = []
    for current_f2mt in _field_to_mapping_table:
        current_field = current_f2mt[0]
        current_mt = current_f2mt[1]
        stmt = f"""
        alter table {current_mt} set unlogged;
        with to_match as (
            -- retrieve values that need matching and their
            -- existing match_ids from mapping table if found
            select
                {', '.join(
                    [f'''{f}, {m}.prev_match_id as {f}_prev_match_id, {m}.match_id as {f}_match_id,
                        tmp.datetime as {f}_datetime, tmp.source as {f}_source'''
                        for f, m in [current_f2mt] + to_check]
                )}
            from tmp
            -- join to retrieve match_ids for current and priority fields
            {' '.join(
                [f'''left join {m} using ({f})''' for f, m in to_check + [current_f2mt]]
            )}
        ), existing_impacted as (
            -- retrieve values from mapping tables that will be impacted by changes in match_ids
            select
                {', '.join(
                    [f'''{f}, {m}.match_id as {f}_match_id, {m}.datetime as {f}_datetime,
                        {m}.source as {f}_source''' for f, m in [current_f2mt] + to_check]
                )}
            from {current_mt}
            /* join on previous_match_ids because priority_fields are already
             * recalculated and prev_match_id equals match_id when new priority_field created
             */
            {' '.join(
                [f'''left join {m} on {m}.prev_match_id = {current_mt}.match_id
                    ''' for _, m in to_check]
            )}
            /*
             * only include rows that are impacted by priority_field match_id reassignments
             * i.e. priority_field prev_match_id matches current_field match_id
             *
             * example1 (on update 'dun'): (format - 'field': prev_match_id, match_id)
             *      existing : 'ch1': 1,1, 'dun1': 1,1(a1), 'name1': 1,1
             *                 'ch2': 2,2, 'dun2': 2,2(a2)
             *                 'ch3': 3,3 (changes from ch update)
             *      to_match : 'ch3': 3,3, 'dun1': 1,1(b), 'name1': 1,1 (lookup ids)
             * => 'ch1' row needs to be included (a == b), 'ch2' row does not
             *
             * example2 (on update 'name'):
             *      existing : 'ch1': 1,1, 'dun1': 1,1, 'name1': 1,1(a)
             *                 'ch2': 2,2, 'dun1': 1->1,1->2 (changes from ch/dun update)
             *      to_match : 'ch2': 2,2, 'dun1': 1(b),2,  null
             * => 'name1' row needs to be included (a == b (coalesce(null, 1)))
             */
            inner join (
                select
                    coalesce({', '.join(
                        [f'''{current_field}_match_id'''] +
                        [f'''{f}_prev_match_id''' for f, _ in to_check[::-1]]
                    )})::int as match_id
                from to_match
            ) sq on sq.match_id = {current_mt}.match_id
        ), latest_values as (
            select distinct on ({current_field})
                {current_field},
                {current_field}_datetime,
                {current_field}_source,
                {', '.join(
                    [f'{current_field}_match_id'] +
                    [f'''first_value({f}_match_id) over
                    (PARTITION BY {current_field} ORDER BY {f} IS NULL, {f}_datetime desc)
                    -- IS NULL evaluates to TRUE or FALSE. FALSE sorts before TRUE.
                    -- This way, non-null values come first
                    as {f}_match_id''' for f, _ in to_check]
                )} -- only latest values are relevant to calculate match_id
            from (
                -- values from the new descriptions
                select
                    {', '.join(
                        [f'''{f}, {f}_match_id, {f}_datetime, {f}_source'''
                            for f, _ in [current_f2mt] + to_check]
                    )} from to_match
                -- add impacted existing fields (not required for first field)
                {'union (select * from existing_impacted)' if to_check else ''}
            ) sq
            where {current_field} is not null
            order by {current_field}, {current_field}_datetime desc
        )
        insert into {current_mt}
            -- if no prev_match_id exists use the current one
            select
                field,
                coalesce(prev_match_id, new_match_id) as prev_match_id,
                new_match_id,
                source,
                datetime
            from (
                select
                    lv.{current_field} as field,
                    lv.{current_field}_source as source,
                    lv.{current_field}_datetime as datetime,
                    /*
                     * find match_ids from left to right, if non found check
                     * existing match_id for current field or create new
                     */
                    coalesce({', '.join(
                        [f'''{f}_match_id''' for f, _ in to_check + [current_f2mt]]
                    )}, nextval('match_id_seq')) as new_match_id,
                    lv.{current_field}_match_id as prev_match_id
                from latest_values lv
                order by lv.{current_field}_datetime asc -- calculate oldest records first
            ) SQ
            where prev_match_id is null or prev_match_id != new_match_id
        -- if field value already exists in mapping table, update the match_id with the newer ones
        on conflict ({current_field}) do update set
            prev_match_id=EXCLUDED.prev_match_id,
            match_id=EXCLUDED.match_id,
            source=EXCLUDED.source,
            datetime=EXCLUDED.datetime;
        alter table {current_mt} set logged;
        """
        to_check.append((current_field, current_mt))
        db_utils.execute_statement(stmt)


def get_match_ids(dnb_match=False):
    stmt = f"""
    select {'distinct on (id)' if dnb_match else ''}
                -- select most recent dnb number in match group
        id,
        {'coalesce(SQ.duns_number, duns_number_mapping.duns_number)'
            if dnb_match else 'aggr_match_id'},
        concat(
            {','.join(
                [
                    f'CASE WHEN {f}_match_id = aggr_match_id THEN 1 ELSE 0 END'
                    for f, _ in _field_to_mapping_table
                ]
            )}
        ) as similarity
    from (
        select
            t1.id,
            {'t1.duns_number,' if dnb_match else ''}
            {','.join(f'{f}_mapping.match_id as {f}_match_id' for f, _ in _field_to_mapping_table)},
            coalesce({','.join(
                [f'{f}_mapping.match_id' for f, _ in _field_to_mapping_table]
            )}) as aggr_match_id
        from tmp t1
            {' '.join(
                [
                    f'left join {mt} {f}_mapping using ({f})' for f, mt in _field_to_mapping_table
                ]
            )}
    ) SQ
    {f'''left join duns_number_mapping on duns_number_mapping.match_id = aggr_match_id
    order by id asc, duns_number_mapping.datetime desc''' if dnb_match else 'order by id asc'}
    """
    return db_utils.execute_query(stmt)
