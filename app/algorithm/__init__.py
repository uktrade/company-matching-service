from app.algorithm import sql_statements as sql
from app.algorithm.sql_statements import json_to_tmp_table, get_match_ids, update_company_descriptions, update_mappings


class Matcher:

    def match(self, json_data, update=True, match=True):
        json_to_tmp_table(json_data)
        if update:
            update_company_descriptions()
            update_mappings()
        if match:
            return get_match_ids()
        else:
            return []
