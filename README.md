[![Build Status](https://travis-ci.com/BookOps-CAT/bookops-nypl-platform.svg?branch=master)](https://travis-ci.com/BookOps-CAT/bookops-nypl-platform) [![Coverage Status](https://coveralls.io/repos/github/BookOps-CAT/bookops-nypl-platform/badge.svg?branch=master)](https://coveralls.io/github/BookOps-CAT/bookops-nypl-platform?branch=master) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# bookops-nypl-platform client
BookOps Python wrapper around NYPL Platform API

Requries Python 3.7 & up.

WORK-IN-PROGRESS

Bookops-nypl-platform client provides a Python interface for the internal NYPL Platform API.
It provides functionality relevant to BookOps and is not a full implementaiton of NYPL Platform API.

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

## Changelog


## References
+ [NYPL Platform API Swagger](https://platformdocs.nypl.org/)
+ [NYPL Platform API Documentation](https://docs.google.com/document/d/1p3q9OT9latXqON20WDh4CNPxIShUunfGgqT163r-Caw/edit?usp=sharing)
+ [ruby-nypl-platfom-api-client](https://github.com/NYPL/ruby-nypl-platform-api-client)
