# Company Matching Service

Matches companies between different datasets

## Match [POST /api/v1/company/match/]

+ Parameters

    + **dnb_match** If true, the provided data will be matched against a D&B number instead of a match_id

+ Body
        
        {
            "descriptions": [
                {
                    "id": "1", 
                    "companies_house_id": "05588682",
                    "duns_number": "d210"
                    "company_name":"apple", 
                    "contact_email": "john@apple.com",
                    "cdms_ref": "782934",
                    "postcode": "SW129RP",
                },
                {
                    "id": "2", 
                    "companies_house_id": "05588683",
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
                    "id": "1",
                    "match_id": 1,
                    "similarity": "110000"
                },
                {
                    "id": "2",
                    "match_id": 1,
                    "similarity": "101000"
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
    + **dnb_match** If true, the provided data will be matched against a D&B number instead of a match_id

    
+ Body
        
        {
            "descriptions": [
                {
                    "id": "1",
                    "source": "dit.datahub",
                    "datetime": "2019-01-01 00:00:00", 
                    "company_name":"apple", 
                    "companies_house_id": "05588682"
                },
                {
                    "id": "2",
                    "source": "dit.export-wins"
                    "datetime": "2018-01-01 00:00:00", 
                    "companies_house_id": "05588682"
                }
            ]
        }
        
+ Headers
    
    + Authorization: Hawk id="dh37fgj492je", ts="1353832234", nonce="j4h3g2", mac="6R4rV5iE+NPoym+WwjeHzjAGXUtLNIxmo1vpMofpLAE="

+ Response 200 (application/json)

        {
            "matches": [
                {
                    "id": "1",
                    "match_id": 1,
                    "similarity": "110000"
                },
                {
                    "id": "2",
                    "match_id": 1,
                    "similarity": "100000"
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

## Authorization

The endpoints are secured with Hawk Authentication (https://github.com/hueniverse/hawk). To use a secured endpoint an id and secret is required. Below an example how the authorization header can be generated in Python.

+ Example usage Python
        
        import json
        
        import requests
        from mohawk import Sender
    
        url = 'company-matching-service-staging.london.cloudapps.digital/api/v1/company/match/'
        json_query = {
            "descriptions": [
                {
                    "id": "1",
                    "source": "dit.datahub",
                    "datetime": "2019-01-01 00:00:00", 
                    "company_name":"apple", 
                    "companies_house_id": "05588682"
                },
            ]
        }

        def get_sender(url, json_query):
            json_data = json.dumps(json_query)
            
            return Sender(
                credentials={
                    'id': 'test_user',
                    'key': 'secret1',
                    'algorithm': 'sha256'
                },
                url=url,
                method='POST',
                content=json_data,
                content_type='application/json',
            )

        response = requests.post(
            url,
            headers={'Authorization': get_sender(url, json_query).request_header},
            json=json_query
        )
        assert response.status_code == 200
        assert json.loads(response.text) == {
            "matches": [
                {
                    "id": 1,
                    "match_id": 1,
                    "similarity": "101000"
                },
            ]
        }
