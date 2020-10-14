[![Build Status](https://travis-ci.com/BookOps-CAT/bookops-nypl-platform.svg?branch=master)](https://travis-ci.com/BookOps-CAT/bookops-nypl-platform) [![Coverage Status](https://coveralls.io/repos/github/BookOps-CAT/bookops-nypl-platform/badge.svg?branch=master)](https://coveralls.io/github/BookOps-CAT/bookops-nypl-platform?branch=master) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# bookops-nypl-platform client
BookOps Python wrapper around NYPL Platform API

Requries Python 3.7 & up.


bookops-nypl-platform client provides a Python interface for the internal NYPL Platform API.
It provides functionality relevant to BookOps and is not a full implementation of the NYPL Platform API.

## Version

> 0.1.0

## Basic usage
**Access Token**

```python
>>>from bookops_nypl_platform import PlatformToken
>>>token=PlatformToken("my_client_id", "my_client_secret", "oauth_server")
>>>print(token)
"<token: token_string_here, expires_on: 2019-01-01 17:59:59, token_request_response: {'access_token': 'token_string_here', 'expires_in': 3600, 'token_type': 'Bearer', 'scope': 'scopes_here', 'id_token': 'token_string_here'}>"
```

**Retrieve bibs by ISBN**
```python
>>>from bookops_nypl_platform import PlatformSession
>>>session = PlatformSession(authorization=token, agent="my_client")
>>>response = session.search_standardNos(keywords=["9780316230032", "0674976002"])
>>>print(response.status_code)
200
>>>print(response.json()) 
```
```json
{
    "data": [
        {
            "id": "21790265",
            "nyplSource": "sierra-nypl",
            "nyplType": "bib",
            "updatedDate": "2019-07-30T13:38:44-04:00",
            "createdDate": "2019-04-24T16:27:41-04:00",
            "deletedDate": null,
            "deleted": false,
            "locations": [
                {
                    "code": "mal",
                    "name": "SASB - Service Desk Rm 315"
                },
                {
                    "code": "mal",
                    "name": "SASB - Service Desk Rm 315"
                }
            ],
            "suppressed": false,
            "lang": {
                "code": "eng",
                "name": "English"
            },
            "title": "Blueprint : the evolutionary origins of a good society",
            "author": "Christakis, Nicholas A. author.",
            "materialType": {
                "code": "a",
                "value": "BOOK/TEXT"
            },        
        }
    ],
    "count": 1,
    "totalCount": 0,
    "statusCode": 200,
    "debugInfo": []
}
```

**Retrieve bibs by control numbers**  
context manager:
```python
with PlatformSession(authorization=token) as session:
    response = session.search_controlNos([["1089804986", "1006480637"]])
```

## Changelog


## References
+ [NYPL Platform API Swagger](https://platformdocs.nypl.org/)
+ [NYPL Platform API Documentation](https://docs.google.com/document/d/1p3q9OT9latXqON20WDh4CNPxIShUunfGgqT163r-Caw/edit?usp=sharing)
+ [ruby-nypl-platfom-api-client](https://github.com/NYPL/ruby-nypl-platform-api-client)
