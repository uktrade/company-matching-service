# Company Matching Service

Service to match companies between different data sets

## Installation
The backend is built in Python using the Flask framework. Authentication is implemented using Hawk.

#### Environment

 * Install anaconda 3 and create a new environment:

`conda env create -f environment.yml`

 * Activate environment:

`source activate cms`

#### Config

##### Using docker-compose
1. Copy `.envs/docker.env` to `.env`
2. `docker-compose build`
3. `docker-compose up`
4. Go to http://localhost:5080/healthcheck

##### Using host machine
Config variables can be specified in a few ways and are loaded using the following order of priority:

1. Look for variable in existing System environment variables
2. If not found in step 1, look for variable in `.env` (this only works if USE_DOTENV is set to 1, see .envs/sample.env for an example file)
3. If not found in step 2, look for variable in `local_testing.yml` (this only works if TESTING is set to 1)
4. If not found in step 3, look for variable in `local.yml` (this only works if TESTING is set to 0)
5. If not found in step 4, look for variable in `default.yml`

#### Running tests

`make run_tests`

## Commands

#### If using docker enter the running web container to run commands
`docker exec -ti data_cms_web_1 /bin/bash`

#### Initialize tables
`python manage.py dev db --create_tables`

#### Add hawk users
`python manage.py dev add_hawk_user --client_id=<client_id> --client_key=<client_key> --client_scope=* --description=data-flow`

## API

see API.md

## Matching Algorithm

The matching algorithm matches company descriptions consisting of at least one of the following attributes:

* companies house id: 8 character numeric identifier for a company registered with Companies House in the United Kingdom
* duns number: a nine-digit long number that is used to identify your business by Dun and Bradstreet
* company name: the name of the business
* contact email: an email address of an employee of the business 
* CDMS reference: references used in the old Customer Data Management System at DIT
* company address postcode: Postcode of the business trading address

The attributes above are listed in order of priority. e.g. if two descriptions have the same companies house id, the likelihood of being the same company is higher then having the same trading address.

#### Clustering

In order to match new company descriptions, the backend of the service needs to store information of existing companies to match against.

The update API endpoint can be used for this purpose. Only trusted services that can provide quality company information are supposed to use this endpoint. The provided information will be used by the algorithm to improve its matching results. 

The algorithm creates a tree from the descriptions that clusters companies in different groups. Each group gets assigned a specific id called a match_id. 

EXAMPLE 1 - Suppose the following descriptions are provided:
- description 1:
    * companies_house_id: 1
    * company_name: company x
- description 2:
    * companies_house_id: 2
    * company_name: company y
- description 3:
    * companies_house_id: 2
    * duns_number: 1
    
This will result in the following tree with two clusters (match_id 1,2):

```
├── match_id 1
│   ├── ch_id 1
│       ├── name: company x
├── match_id 2
│   ├── ch_id 2
│       ├── duns: 1
│           ├── name: company y
```

Because information changes over time (for example, companies cease to exist and other companies can potentially reuse an existing name), the supplied information requires a mandatory timestamp. Newer information will have priority over older information.

EXAMPLE 2 - Suppose the following description is provided:
- description 1:
    * timestamp: 01/01/2019
    * companies_house_id: 1
    * company_name: company x

With corresponding tree:

```
├── match_id 1
│   ├── ch_id 1 (01/01/2019)
│       ├── name: company x (01/01/2019)
```

When a newer description 2 is provided that specifies that company_name x now belongs to companies_house_id 2.

- description 2:
    * timestamp: 01/01/2020
    * companies_house_id: 2
    * company_name: company x

The tree will be updated as follows:

```
├── match_id 1
│   ├── ch_id 1 (01-01-2019)
├── match_id 2
│   ├── ch_id 2 (01-01-2020)
│       ├── name: company x (01-01-2020)
```

#### Matching

The matching endpoint can be used to match descriptions against the existing decision tree. When using this endpoint, no new information will be stored in the backend.

EXAMPLE 3 - Assuming the following tree exists in the backend:

```
├── match_id 1
│   ├── ch_id 1
│       ├── name: company x
├── match_id 2
│   ├── ch_id 2
│       ├── duns: 1
│           ├── name: company y
```

When submitting the following descriptions to the matching endpoint (a unique user defined id needs to be specified to be able to link the response and the request descriptions)
:

- description 1:
    * id: 1
    * companies_house_id: 1
    * company_name: company x
- description 2:
    * id: 2
    * companies_house_id: 2
    * company_name: company x


The matching algorithm will match against the existing tree and return the following response:

```
{
    "matches": [
        {
            "id": 1,
            "match_id": 1,
            "similarity": "101000"
        },
        {
            "id": 2,
            "match_id": 2,
            "similarity": "100000"
        }                
    ]
}
```

The match_id corresponds to the cluster where the matching algorithm decides the description belongs to. A 6 digit similarity string is also provided on how accurate the match is. A '1' digit in the similarity string indicates that a match was found on the corresponding attribute (pos 1: companies house id, pos 2: dun & bradstreet number, pos 3: company name, pos 4: contact email domain, pos 5: cdms reference, pos 6: company address postcode). 

The description with id 1 is matched to cluster with match_id 1 with both companies_house_id and company_name matching. The description with id 2 matches match_id 2 (not 1 because companies_house_id has priority over company_name) but the similarity string has a zero in position 3 because the name doesn't belong to this cluster.

It is also worth noting that transformations are done on some attributes before matching:
* all attribute data is converted to lowercase
* company names will be simplified. for example keywords like limited or ltd at the end will be stipped out.
* only the email domain is used for matching contact emails
* cmds reference are simplified to only constist of digits
* spaces in a postcode will be removed