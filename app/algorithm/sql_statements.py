import json

from app.db import db_utils
from app.db.models import *


_ch_name_simplification = """
    lower(coalesce( nullif(
        regexp_replace(
        regexp_replace(
          company_name,
          '^the\s|\s?:\s?|\[|\]|\(|\)|\'\'|\*.*\*|&|,|;|"|ltd\.?$|limited\.?$|\sllp\.?$|\splc\.?$|\sllc\.?$|\sand\s|\sco[\.|\s]|\scompany[\s|$]', ' ', 'gi'),
          '\.|\s', '', 'gi')
      , ''), company_name))
"""

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
"""

_field_to_mapping_table = [
    ('companies_house_id', CompaniesHouseIDMapping.__tablename__),
    ('duns_number', DunsNumberMapping.__tablename__),
    ('name_simplified', CompanyNameMapping.__tablename__),
    ('contact_email_domain', ContactEmailMapping.__tablename__),
    ('cdms_ref_cleaned', CDMSRefMapping.__tablename__),
    ('postcode', PostcodeMapping.__tablename__),
]


def json_to_tmp_table(json_data):
    stmt = """
        DROP TABLE IF EXISTS tmp;
        CREATE TEMPORARY TABLE tmp (
            desc_id int,
            id text,
            source text,
            datetime timestamp,           
            companies_house_id text,
            duns_number text,
            company_name text,
            contact_email text,
            cdms_ref text,
            postcode text,
            name_simplified text,
            cdms_ref_cleaned text,
            contact_email_domain text
        );
    """
    db_utils.execute_statement(stmt)
    stmt = f"""
        INSERT INTO tmp (  
            desc_id,  
            id,
            source,
            datetime,
            companies_house_id,
            duns_number,
            company_name,
            contact_email,
            cdms_ref,
            postcode,
            name_simplified,
            cdms_ref_cleaned,
            contact_email_domain
        )
        SELECT
            nextval('company_description_id_seq'),
            id,
            source,
            datetime,
            companies_house_id,
            duns_number,
            company_name,
            contact_email,
            cdms_ref,
            postcode,
            {_general_name_simplification},
            regexp_replace(cdms_ref, '\D','','g'),
            lower(split_part(contact_email, '@', 2)) AS contact_email_domain
            
        FROM json_populate_recordset(null::tmp, %s);
    """
    db_utils.execute_statement(stmt, (json.dumps(json_data), ))


def update_company_descriptions():
    stmt = f"""
    insert into {CompanyDescriptionModel.__tablename__}
    (   
        id,
        data_hash,
        source,
        datetime,
        companies_house_id,
        duns_number,
        company_name,
        contact_email,
        cdms_ref,
        postcode
    )
    select
        desc_id,
        md5(
            ROW(
                source::text,
                datetime::text,
                companies_house_id::text,
                duns_number::text,
                company_name::text,
                contact_email::text,
                cdms_ref::text,
                postcode::text
            )::TEXT
        ) as data_hash,
        source,
        datetime,
        companies_house_id,
        duns_number,
        company_name,
        contact_email,
        cdms_ref,
        postcode
    from tmp
    on conflict (data_hash) do nothing;
    commit; """
    db_utils.execute_statement(stmt)


def update_mappings():
    to_check = []
    for current_f2mt in _field_to_mapping_table:
        current_field = current_f2mt[0]
        current_mt = current_f2mt[1]
        stmt = f"""
        alter table {current_mt} set unlogged;
        with unmatched as (
            select distinct on (t1.{current_field})
                t1.desc_id, 
                t1.datetime,
                {','.join(
                    [f't1.{current_field}'] +
                    [f'''first_value(t1.{f}) over
                    (PARTITION BY t1.{current_field} ORDER BY t1.{f} IS NULL, t1.datetime desc)
                    -- IS NULL evaluates to TRUE or FALSE. FALSE sorts before TRUE. This way, non-null values come first
                    as {f}''' for f, _ in to_check]
                )} -- only latest value from rows of some field value are relevant to calculate match_id
            from tmp t1
                left join {current_mt} t2 using ({current_field})
                left join {CompanyDescriptionModel.__tablename__} t3 on t2.id = t3.id 
                -- join to retrieve timestamp
            where t1.{current_field} is not null
                and (t2.{current_field} is null or t3.datetime < t1.datetime)
                -- update mapping if current info is new or more recent
            order by t1.{current_field}, t1.datetime desc
            -- only most recent info is relevant in case of multiple duplicate values for current field
        )
        insert into {current_mt}
            select u.{current_field}, coalesce({','.join(
                [f'''{f}_mapping.match_id''' for f, _ in to_check[::-1] + [current_f2mt]]
            )}, nextval('match_id_seq')) as match_id, u.desc_id from unmatched u
            -- find match_ids from right to left, if non found check existing match_id for current field or create new 
            {' '.join(
                [f'''left join {m} {f}_mapping using ({f})''' for f, m in to_check + [current_f2mt]]
            )}
            -- join to retrieve match id for priority fields
            order by u.datetime asc
            -- update oldest records first
        on conflict ({current_field}) do update set match_id=EXCLUDED.match_id, id=EXCLUDED.id; 
        -- if field value already exists in mapping table, update the match_id and timestamp with the newer ones   
        alter table {current_mt} set logged;
        commit; 
        """
        to_check.append((current_field, current_mt))
        db_utils.execute_statement(stmt)


def get_match_ids():
    stmt = f"""
    select 
        id, 
        aggr_match_id, 
        concat(
            {','.join([f'CASE WHEN {f}_match_id = aggr_match_id THEN 1 ELSE 0 END' for f, _ in _field_to_mapping_table])}
        ) as similarity
    from (
        select
            t1.id,
            {','.join(f'{f}_mapping.match_id as {f}_match_id' for f, _ in _field_to_mapping_table)},
            coalesce({','.join(
                [f'{f}_mapping.match_id' for f, _ in _field_to_mapping_table]
            )}) as aggr_match_id
        from tmp t1
            {' '.join([f'left join {mt} {f}_mapping using ({f})' for f, mt in _field_to_mapping_table])}
    ) SQ;
    """
    return db_utils.execute_query(stmt)

