# Company Matching Service

Matches companies between different datasets

## Match [POST /api/v1/company/match/]

+ Parameters

+ Body
        
        {
            "descriptions": [
                {
                    "id": 1, 
                    "companies_house_id": "0921309",
                    "duns_number": "d210"
                    "company_name":"apple", 
                    "contact_email": "john@apple.com",
                    "cdms_ref": "782934",
                    "postcode": "SW129RP",
                },
                {
                    "id": 2, 
                    "companies_house_id": "0921309",
                    "company_name":"new apple", 
                }
            ]
        }
        
+ Headers
    
    + Authorization: Hawk id="dh37fgj492je", ts="1353832234", nonce="j4h3g2", mac="6R4rV5iE+NPoym+WwjeHzjAGXUtLNIxmo1vpMofpLAE="

+ Response 200 (application/json)
        
        {
            "matches": [
                {
                    "id": 1,
                    "match_id": 1,
                    "similarity": "100000"
                },
                {
                    "id": 2,
                    "match_id": 1,
                    "similarity": "110000"
                }                
            ]
        }

+ Response 404 (application/json)

    + Headers
    + Body

            {}

+ Response 400 (application/json)

    + Headers
    + Body

            {
                error: 'error_message'
            }

+ Response 401

    + Headers
    + Body

+ Response 500

    + Headers
    + Body


## Upload [POST /api/v1/company/update/]

+ Parameters

    + **match** If false, the provided data will not be matched and a 204 will be returned.
    
+ Body
        
        {
            "descriptions": [
                {
                    "id": 1,
                    "source": "dit.datahub",
                    "datetime": "2019-01-01 00:00:00", 
                    "company_name":"apple", 
                    "companies_house_id": "0921309"
                },
                {
                    "id": 2,
                    "source": "dit.export-wins"
                    "datetime": "2018-01-01 00:00:00", 
                    "companies_house_id": "0966666"
                }
            ]
        }
        
+ Headers
    
    + Authorization: Hawk id="dh37fgj492je", ts="1353832234", nonce="j4h3g2", mac="6R4rV5iE+NPoym+WwjeHzjAGXUtLNIxmo1vpMofpLAE="

+ Response 200 (application/json)

        {
            "matches": [
                {
                    "id": 1,
                    "match_id": 1,
                    "similarity": "01000000"
                },
                {
                    "id": 2,
                    "match_id": 2,
                    "similarity": "11000000"
                }                
            ]
        }

+ Response 204

    + Headers
    + Body

+ Response 404 (application/json)

    + Headers
    + Body

            {}

+ Response 400 (application/json)

    + Headers
    + Body

            {
                error: 'error_message'
            }

+ Response 401

    + Headers
    + Body

+ Response 500

    + Headers
    + Body

