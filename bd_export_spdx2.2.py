#!/usr/bin/env python
import logging
import sys
import os

from blackduck import Client
from export_spdx import globals
from export_spdx import config
from export_spdx import main

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', stream=sys.stderr, level=logging.INFO)
logging.getLogger("requests").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

url = os.environ.get('BLACKDUCK_URL')
if config.args.blackduck_url:
    url = config.args.blackduck_url

api = os.environ.get('BLACKDUCK_API_TOKEN')
if config.args.blackduck_api_token:
    api = config.args.blackduck_api_token

if config.args.blackduck_trust_certs:
    globals.verify = False

if url == '' or url is None:
    print('BLACKDUCK_URL not set or specified as option --blackduck_url')
    sys.exit(2)

if api == '' or api is None:
    print('BLACKDUCK_API_TOKEN not set or specified as option --blackduck_api_token')
    sys.exit(2)

globals.bd = Client(
    token=api,
    base_url=url,
    verify=globals.verify,  # TLS certificate verification
    timeout=config.args.blackduck_timeout
)

if __name__ == "__main__":
    main.run()
