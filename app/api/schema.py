COMPANY_MATCH_BODY = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Matching query",
    "description": "A query to retrieve match_ids from company descriptions",
    "type": "object",
    "properties": {
        "descriptions": {
            "type": "array",
            "items": {
                "type": "object",
                "minLength": 1,
                "properties": {
                    "id": {
                        "type": "string",
                        "minLength": 1
                    },
                    "company_name": {
                        "type": "string",
                        "minLength": 1
                    },
                    "companies_house_id": {
                        "type": "string",
                        "minLength": 8,
                        "maxLength": 8
                    },
                    "duns_number": {
                        "type": "string",
                        "minLength": 1
                    },
                    "contact_email": {
                        "type": "string",
                        "pattern": "[^@]+@[^@]+\.[^@]+"
                    },
                    "postcode": {
                        "type": "string",
                        "minLength": 1
                    },
                    "cdms_ref": {
                        "type": "string",
                        "minLength": 1
                    },
                },
                "required": ["id"],
                "anyOf": [
                    {"required": ["company_name"]},
                    {"required": ["companies_house_id"]},
                    {"required": ["contact_email"]},
                    {"required": ["postcode"]},
                    {"required": ["duns_number"]},
                    {"required": ["cdms_ref"]},
                ],
            },
        },
    },
    "required": ["descriptions"],
}

COMPANY_UPDATE_BODY = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Matching query",
    "description": "A query to store company descriptions used for future matching",
    "type": "object",
    "properties": {
        "descriptions": {
            "type": "array",
            "items": {
                "type": "object",
                "minLength": 1,
                "properties": {
                    "id": {
                        "type": "string",
                        "minLength": 1
                    },
                    "company_name": {
                        "type": "string",
                        "minLength": 1
                    },
                    "companies_house_id": {
                        "type": "string",
                        "minLength": 8,
                        "maxLength": 8
                    },
                    "duns_number": {
                        "type": "string",
                        "minLength": 1
                    },
                    "contact_email": {
                        "type": "string",
                        "pattern": "[^@]+@[^@]+\.[^@]+"
                    },
                    "postcode": {
                        "type": "string",
                        "minLength": 1
                    },
                    "cdms_ref": {
                        "type": "string",
                        "minLength": 1
                    },
                },
                "required": ["id", "datetime", "source"],
                "anyOf": [
                    {"required": ["company_name"]},
                    {"required": ["companies_house_id"]},
                    {"required": ["contact_email"]},
                    {"required": ["postcode"]},
                    {"required": ["duns_number"]},
                    {"required": ["cdms_ref"]},
                ],
            },
        },
    },
    "required": ["descriptions"],
}
