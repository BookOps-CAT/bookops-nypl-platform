![tests](https://github.com/BookOps-CAT/bookops-nypl-platform/actions/workflows/unit-tests.yaml/badge.svg?branch=master) [![Coverage Status](https://coveralls.io/repos/github/BookOps-CAT/bookops-nypl-platform/badge.svg?branch=master)](https://coveralls.io/github/BookOps-CAT/bookops-nypl-platform?branch=master) ![GitHub tag (latest SemVer)](https://img.shields.io/github/v/tag/BookOps-CAT/bookops-nypl-platform) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# bookops-nypl-platform client
BookOps Python wrapper around NYPL Platform API

Requries Python 3.8 & up.


bookops-nypl-platform client provides a Python interface for the internal NYPL Platform API.
It provides functionality relevant to BookOps and is not a full implementation of the NYPL Platform API.

## Version

> 0.5.0

## Installation

Install via pip:

```bash
python -m pip install git+https://github.com/BookOps-CAT/bookops-nypl-platform
```

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

### [0.5.0] - 2024-11-25
#### Added
 + `.flake8` file to ignore line length and unused import errors in tests
 + Python versions 3.11, 3.12, and 3.13 to GitHub Actions
 + `BookopsPlatformError` as top level import
 + `py.typed` file so applications using `bookops-nypl-platform` will use annotations from this package
 + added type annotations where they were missing and fixed them where they were incomplete or inaccurate
 + type annotations to variables in `PlatformSession` methods where needed
 + Dev dependencies:
   + `exceptiongroup` (1.2.2)

#### Changed
 + updated GitHub checkout and setup actions in automated tests (`unit-tests.yaml`)
 + `if type() is` type check syntax changed to `isinstance` type checks
 + target python version in `pyproject.toml` now 3.8-3.13
 + Updated dependencies:
   + `certifi` (2024.8.30)
   + `charset-normalizer` (3.4.0)
   + `idna` (3.10)
   + `requests` (2.32.3)
   + `urllib3` (2.2.3)
 + Updated dev dependencies:
   + `black` (24.8.0)
   + `coverage` (7.6.1)
   + `packaging` (24.2)
   + `pathspec` (0.12.1)
   + `platformdirs` (4.3.6)
   + `pluggy` (1.5.0)
   + `pytest-cov` (5.0.0)
   + `pytest-mock` (3.14.0)
   + `pytest` (8.3.3)
   + `tomli` (2.1.0)
   + `typing-extensions` (4.12.2)

#### Fixed
 + default value for `PlatformToken.timeout` and `PlatformSession.timeout` is now `(3,3,)`. Removed conditional check from `__init__.py` for both classes that set the `timeout` value if `timeout` was `None`
 + typo in docstring of `authorize.py`
 + changed names of variables in `PlatformSession` methods where they were the same as names of a param passed to that method. Certain variables have different types than the params with the same name which caused errors with the type checker. See `keywords` param/variable in `PlatformToken.search_standardNos` and `keyword`/`standardNos` variable

#### Removed
 + support for Python 3.7
 + `Type` no longer used in type annotations 
 + implicit optional types changed to explicit `Optional` with `None` as default value
 + Dev dependencies:
   + `mike`
   + `mkdocs`
   + `mkapi`
 + `pytest.ini` file. Moved to `pytest.ini_options` in `pyproject.toml`


### [0.4.0] - 2023-12-28

#### Changed
  + `conftest.py` updated path to credentials
  + dependencies:
    + certifi (2023.11.17)
    + requests (2.31.0)
  + dev dependencies:
    + black (22.12.0)
    + mike (0.5.5)
    + mkapi (1.0.14)
    + mkdocs (1.5.3)
    + pytest (6.2.5)
    + pytest-cov (2.12.1)
    + pytest-mock (3.11.1)

### [0.3.0] - 2022-02-05

#### Changed
  + Dependencies update:
    + requests to 2.27.1
    + urllib3 to 1.26.8
    + dev dependencies update
  + CI moved to Github-Actions
    + adds Python 3.10

### [0.2.1] - 2021-10-29

#### Fixed
  + Metadata fixes in pyproject.toml to indicate the client supports Python 3.7

#### Changed
  + Dependencies updates

### [0.2.0] - 2020-10-27

#### Added
  + /v0.1/items `get_item_list` a method to retrieve a list of item records

## References
+ [NYPL Platform API Swagger](https://platformdocs.nypl.org/)
+ [NYPL Platform API Documentation](https://docs.google.com/document/d/1p3q9OT9latXqON20WDh4CNPxIShUunfGgqT163r-Caw/edit?usp=sharing)
+ [ruby-nypl-platfom-api-client](https://github.com/NYPL/ruby-nypl-platform-api-client)

[0.5.0]: https://github.com/BookOps-CAT/bookops-nypl-platform/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/BookOps-CAT/bookops-nypl-platform/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/BookOps-CAT/bookops-nypl-platform/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/BookOps-CAT/bookops-nypl-platform/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/BookOps-CAT/bookops-nypl-platform/compare/v0.1.0...v0.2.0