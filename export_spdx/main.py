#!/usr/bin/env python
import logging
import sys
import os
import datetime

from blackduck import Client
from export_spdx import globals
from export_spdx import spdx
from export_spdx import config
from export_spdx import process
from export_spdx import projects

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', stream=sys.stderr, level=logging.INFO)
logging.getLogger("requests").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

url = os.environ.get('BLACKDUCK_URL')
if config.args.blackduck_url:
    url = config.args.blackduck_url

api = os.environ.get('BLACKDUCK_API_TOKEN')
if config.args.blackduck_api_token:
    api = config.args.blackduck_api_token

exclude_ignored_components = os.environ.get('EXCLUDE_IGNORED_COMPONENTS')
if config.args.exclude_ignored_components:
    exclude_ignored_components = config.args.exclude_ignored_components

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


def run():
    print("BLACK DUCK SPDX EXPORT SCRIPT VERSION {}\n".format(globals.script_version))

    config.check_params()

    project, version = projects.check_projver(config.args.project_name, config.args.project_version)
    print("Working on project '{}' version '{}'\n".format(project['name'], version['versionName']))

    bearer_token = globals.bd.session.auth.bearer_token

    if config.args.recursive:
        globals.proj_list = projects.get_all_projects()

    globals.spdx_custom_lics = []

    toppackage = spdx.clean_for_spdx("SPDXRef-Package-" + project['name'] + "-" + version['versionName'])
    mytime = datetime.datetime.now()

    # Define TOP Document entries
    globals.spdx["SPDXID"] = "SPDXRef-DOCUMENT"
    globals.spdx["spdxVersion"] = "SPDX-2.2"
    globals.spdx["creationInfo"] = {
        # "created": spdx.quote(version['createdAt'].split('.')[0] + 'Z'),
        "created": spdx.quote(mytime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
        "creators": ["Tool: Black Duck SPDX export script https://github.com/matthewb66/bd_export_spdx2.2"],
        "licenseListVersion": "3.9",
    }
    if 'description' in project.keys():
        globals.spdx["creationInfo"]["comment"] = spdx.quote(project['description'])
    globals.spdx["name"] = spdx.quote(project['name'] + '/' + version['versionName'])
    globals.spdx["dataLicense"] = "CC0-1.0"
    globals.spdx["documentDescribes"] = [toppackage]
    globals.spdx["documentNamespace"] = version['_meta']['href']
    globals.spdx["downloadLocation"] = "NOASSERTION"
    globals.spdx["filesAnalyzed"] = False
    globals.spdx["copyrightText"] = "NOASSERTION"
    globals.spdx["externalRefs"] = [
                {
                    "referenceCategory": "OTHER",
                    "referenceType": "BlackDuckHub-Project",
                    "referenceLocator": project["_meta"]["href"],
                },
                {
                    "referenceCategory": "OTHER",
                    "referenceType": "BlackDuckHub-Project-Version",
                    "referenceLocator": version["_meta"]["href"]
                }
            ]

    spdx.add_relationship("SPDXRef-DOCUMENT", toppackage, "DESCRIBES")
    # Add top package for project version
    #
    projpkg = {
        "SPDXID": spdx.quote(toppackage),
        "name": spdx.quote(project['name']),
        "versionInfo": spdx.quote(version['versionName']),
        # "packageFileName":  spdx.quote(package_file),
        "licenseConcluded": "NOASSERTION",
        "licenseDeclared": "NOASSERTION",
        "downloadLocation": "NOASSERTION",
        "packageComment": "Generated top level package representing Black Duck project",
        # PackageChecksum: SHA1: 85ed0817af83a24ad8da68c2b5094de69833983c,
        # "licenseConcluded": spdx.quote(lic_string),
        # "licenseDeclared": spdx.quote(lic_string),
        # PackageLicenseComments: <text>Other versions available for a commercial license</text>,
        "filesAnalyzed": False,
        # "ExternalRef: SECURITY cpe23Type {}".format(cpe),
        # "ExternalRef: PACKAGE-MANAGER purl pkg:" + pkg,
        # ExternalRef: PERSISTENT-ID swh swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2,
        # ExternalRef: OTHER LocationRef-acmeforge acmecorp/acmenator/4.1.3-alpha,
        # ExternalRefComment: This is the external ref for Acme,
        "copyrightText": "NOASSERTION",
        # annotations,
    }
    if 'description' in project.keys():
        projpkg["description"] = spdx.quote(project['description'])
    if 'license' in version.keys():
        if version['license']['licenseDisplay'] == 'Unknown License':
            projpkg["licenseDeclared"] = "NOASSERTION"
        else:
            projpkg["licenseDeclared"] = version['license']['licenseDisplay']
    globals.spdx['packages'].append(projpkg)

    if 'hierarchical-components' in globals.bd.list_resources(version):
        hierarchical_bom = globals.bd.get_resource('hierarchical-components', parent=version)
    else:
        hierarchical_bom = []

    process.process_project(project, version, toppackage, hierarchical_bom, bearer_token, exclude_ignored_components)

    print("Done")

    spdx.write_spdx_file(globals.spdx)


if __name__ == "__main__":
    run()
