from app.algorithm.sql_statements import (
    get_match_ids,
    json_to_tmp_table,
    update_mappings,
)


class Matcher:
    def match(self, json_data, update=True, match=True, dnb_match=False):
        json_to_tmp_table(json_data)
        if update:
            update_mappings()
        if match or dnb_match:
            return get_match_ids(dnb_match=dnb_match)
        else:
            return []
