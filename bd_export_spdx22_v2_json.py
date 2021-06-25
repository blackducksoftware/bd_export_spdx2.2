#!/usr/bin/env python
import argparse
import json
import logging
import sys
import datetime
import os
import re
from lxml import html
import requests
# from zipfile import ZipFile

# from blackduck.HubRestApi import HubInstance
from blackduck import Client

bd = Client(
    token=os.environ.get('BLACKDUCK_API_TOKEN'),
    base_url=os.environ.get('BLACKDUCK_URL'),
    # verify=False  # TLS certificate verification
)

script_version = "0.22 Beta"

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', stream=sys.stderr, level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# hub = HubInstance()

usage_dict = {
    "SOURCE_CODE": "CONTAINS",
    "STATICALLY_LINKED": "STATIC_LINK",
    "DYNAMICALLY_LINKED": "DYNAMIC_LINK",
    "SEPARATE_WORK": "OTHER",
    "MERELY_AGGREGATED": "OTHER",
    "IMPLEMENTATION_OF_STANDARD": "OTHER",
    "PREREQUISITE": "HAS_PREREQUISITE",
    "DEV_TOOL_EXCLUDED": "DEV_TOOL_OF"
}

matchtype_depends_dict = {
    "FILE_DEPENDENCY_DIRECT": "DEPENDS_ON",
    "FILE_DEPENDENCY_TRANSITIVE": "DEPENDS_ON",
}

matchtype_contains_dict = {
    "FILE_EXACT": "CONTAINS",
    "FILE_FILES_ADDED_DELETED_AND_MODIFIED": "CONTAINS",
    "FILE_DEPENDENCY": "CONTAINS",
    "FILE_EXACT_FILE_MATCH": "CONTAINS",
    "FILE_SOME_FILES_MODIFIED": "CONTAINS",
    "MANUAL_BOM_COMPONENT": "CONTAINS",
    "MANUAL_BOM_FILE": "CONTAINS",
    "PARTIAL_FILE": "CONTAINS",
    "BINARY": "CONTAINS",
    "SNIPPET": "OTHER",
}

spdx_deprecated_dict = {
    'AGPL-1.0': 'AGPL-1.0-only',
    'AGPL-3.0': 'AGPL-3.0-only',
    'BSD-2-Clause-FreeBSD': 'BSD-2-Clause',
    'BSD-2-Clause-NetBSD': 'BSD-2-Clause',
    'eCos-2.0': 'NOASSERTION',
    'GFDL-1.1': 'GFDL-1.1-only',
    'GFDL-1.2': 'GFDL-1.2-only',
    'GFDL-1.3': 'GFDL-1.3-only',
    'GPL-1.0': 'GPL-1.0-only',
    'GPL-1.0+': 'GPL-1.0-or-later',
    'GPL-2.0-with-autoconf-exception': 'GPL-2.0-only',
    'GPL-2.0-with-bison-exception': 'GPL-2.0-only',
    'GPL-2.0-with-classpath-exception': 'GPL-2.0-only',
    'GPL-2.0-with-font-exception': 'GPL-2.0-only',
    'GPL-2.0-with-GCC-exception': 'GPL-2.0-only',
    'GPL-2.0': 'GPL-2.0-only',
    'GPL-2.0+': 'GPL-2.0-or-later',
    'GPL-3.0-with-autoconf-exception': 'GPL-3.0-only',
    'GPL-3.0-with-GCC-exception': 'GPL-3.0-only',
    'GPL-3.0': 'GPL-3.0-only',
    'GPL-3.0+': 'GPL-3.0-or-later',
    'LGPL-2.0': 'LGPL-2.0-only',
    'LGPL-2.0+': 'LGPL-2.0-or-later',
    'LGPL-2.1': 'LGPL-2.1-only',
    'LGPL-2.1+': 'LGPL-2.1-or-later',
    'LGPL-3.0': 'LGPL-3.0-only',
    'LGPL-3.0+': 'LGPL-3.0-or-later',
    'Nunit': 'NOASSERTION',
    'StandardML-NJ': 'SMLNJ',
    'wxWindows': 'NOASSERTION'
}

spdx = dict()
spdx['packages'] = []
spdx['relationships'] = []
spdx['snippets'] = []
spdx['hasExtractedLicensingInfos'] = []

parser = argparse.ArgumentParser(description='"Export SPDX for the given project and version"', prog='export_spdx.py')
parser.add_argument("project_name", type=str, help='Black Duck project name')
parser.add_argument("project_version", type=str, help='Black Duck version name')
parser.add_argument("-v", "--version", help="Print script version and exit", action='store_true')
parser.add_argument("-o", "--output", type=str,
                    help="Output SPDX file name (SPDX tag format) - default '<proj>-<ver>.spdx'", default="")
parser.add_argument("-r", "--recursive", help="Scan sub-projects within projects (default = false)",
                    action='store_true')
parser.add_argument("--download_loc",
                    help='''Attempt to identify component download link extracted from Openhub 
                    (slows down processing - default=false)''',
                    action='store_true')
parser.add_argument("--no_copyrights",
                    help="Do not export copyright data for components (speeds up processing - default=false)",
                    action='store_true')
parser.add_argument("--no_files",
                    help="Do not export file data for components (speeds up processing - default=false)",
                    action='store_true')
parser.add_argument("-b", "--basic",
                    help='''Do not export copyright, download link  or package file data (speeds up processing - 
                    same as using "--download_loc --no_copyrights --no_files")''',
                    action='store_true')

args = parser.parse_args()


def clean_for_spdx(name):
    # remove_chars = [';', ':', '!', "*", "(", ")", "/", ","]
    # for i in remove_chars:
    # 	name = name.replace(i, '')
    newname = re.sub('[;:!*()/,]', '', name)
    # replace_chars = [' ', '.']
    # for i in replace_chars:
    # 	name = name.replace(i, '-')
    newname = re.sub('[ .]', '', newname)
    return newname


def quote(name):
    remove_chars = ['"', "'"]
    for i in remove_chars:
        name = name.replace(i, '')
    # return '"' + name + '"'
    return name


def get_all_projects():
    global bd
    # projs = hub.get_projects(5000)
    projs = bd.get_resource('projects', items=True)

    projlist = []
    for proj in projs:
        projlist.append(proj['name'])
    return projlist


def backup_file(filename):
    import os

    if os.path.isfile(filename):
        # Determine root filename so the extension doesn't get longer
        n = os.path.splitext(filename)[0]

        # Is e an integer?
        try:
            root = n
        except ValueError:
            root = filename

        # Find next available file version
        for i in range(1000):
            new_file = "{}.{:03d}".format(root, i)
            if not os.path.isfile(new_file):
                os.rename(filename, new_file)
                print("INFO: Moved old output file '{}' to '{}'\n".format(filename, new_file))
                return new_file
    return ''


def openhub_get_download(oh_url):
    try:
        page = requests.get(oh_url)
        tree = html.fromstring(page.content)

        link = ""
        enlistments = tree.xpath("//a[text()='Project Links:']//following::a[text()='Code Locations:']//@href")
        if len(enlistments) > 0:
            enlist_url = "https://openhub.net" + str(enlistments[0])
            enlist_page = requests.get(enlist_url)
            enlist_tree = html.fromstring(enlist_page.content)
            link = enlist_tree.xpath("//tbody//tr[1]//td[1]/text()")

        if len(link) > 0:
            sp = str(link[0].split(" ")[0]).replace('\n', '')
            #
            # Check format
            protocol = sp.split('://')[0]
            if protocol in ['https', 'http', 'git']:
                return sp

    except Exception as exc:
        print('ERROR: Cannot get openhub data\n' + str(exc))
        return "NOASSERTION"

    return "NOASSERTION"


def get_licenses(lcomp):
    global spdx_custom_lics

    # Get licenses
    lic_string = "NOASSERTION"
    quotes = False
    if 'licenses' in lcomp.keys():
        proc_item = lcomp['licenses']

        if len(proc_item[0]['licenses']) > 1:
            proc_item = proc_item[0]['licenses']

        for lic in proc_item:
            thislic = ''
            if 'spdxId' in lic:
                thislic = lic['spdxId']
                if thislic in spdx_deprecated_dict.keys():
                    thislic = spdx_deprecated_dict[thislic]
            else:
                # Custom license
                try:
                    thislic = 'LicenseRef-' + clean_for_spdx(lic['licenseDisplay'])
                    lic_ref = lic['license'].split("/")[-1]
                    # lic_url = hub.get_apibase() + '/api/licenses/' + lic_ref + '/text'
                    # custom_headers = {'Accept': 'text/plain'}
                    # resp = hub.execute_get(lic_url, custom_headers=custom_headers)
                    headers = {
                        'accept': "text/plain",
                    }
                    # resp = bd.get_json(lic_url, headers=headers)
                    resp = bd.session.get('/api/licenses/' + lic_ref + '/text', headers=headers)
                    resp.raise_for_status()

                    lic_text = resp.content.decode("utf-8")
                    if thislic not in spdx_custom_lics:
                        mydict = {
                            'licenseID': quote(thislic),
                            'extractedText': quote(lic_text)
                        }
                        spdx["hasExtractedLicensingInfos"].append(mydict)
                        spdx_custom_lics.append(thislic)
                except Exception as exc:
                    pass
            if lic_string == "NOASSERTION":
                lic_string = thislic
            else:
                lic_string = lic_string + " AND " + thislic
                quotes = True

        if quotes:
            lic_string = "(" + lic_string + ")"

    return lic_string


spdx_origin_map = {
    "alpine": {"p_type": "apk", "p_namespace": "alpine", "p_sep": "/"},
    "android": {"p_type": "apk", "p_namespace": "android", "p_sep": ":"},
    "bitbucket": {"p_type": "bitbucket", "p_namespace": "", "p_sep": ":"},
    "bower": {"p_type": "bower", "p_namespace": "", "p_sep": "/"},
    "centos": {"p_type": "rpm", "p_namespace": "centos", "p_sep": "/"},
    "clearlinux": {"p_type": "rpm", "p_namespace": "clearlinux", "p_sep": "/"},
    "cpan": {"p_type": "cpan", "p_namespace": "", "p_sep": "/"},
    "cran": {"p_type": "cran", "p_namespace": "", "p_sep": "/"},
    "crates": {"p_type": "cargo", "p_namespace": "", "p_sep": "/"},
    "dart": {"p_type": "pub", "p_namespace": "", "p_sep": "/"},
    "debian": {"p_type": "deb", "p_namespace": "debian", "p_sep": "/"},
    "fedora": {"p_type": "rpm", "p_namespace": "fedora", "p_sep": "/"},
    "gitcafe": {"p_type": "gitcafe", "p_namespace": "", "p_sep": ":"},
    "github": {"p_type": "github", "p_namespace": "", "p_sep": ":"},
    "gitlab": {"p_type": "gitlab", "p_namespace": "", "p_sep": ":"},
    "gitorious": {"p_type": "gitorious", "p_namespace": "", "p_sep": ":"},
    "golang": {"p_type": "golang", "p_namespace": "", "p_sep": ":"},
    "hackage": {"p_type": "hackage", "p_namespace": "", "p_sep": "/"},
    "hex": {"p_type": "hex", "p_namespace": "", "p_sep": "/"},
    "maven": {"p_type": "maven", "p_namespace": "", "p_sep": ":"},
    "mongodb": {"p_type": "rpm", "p_namespace": "mongodb", "p_sep": "/"},
    "npmjs": {"p_type": "npm", "p_namespace": "", "p_sep": "/"},
    "nuget": {"p_type": "nuget", "p_namespace": "", "p_sep": "/"},
    "opensuse": {"p_type": "rpm", "p_namespace": "opensuse", "p_sep": "/"},
    "oracle_linux": {"p_type": "rpm", "p_namespace": "oracle", "p_sep": "/"},
    "packagist": {"p_type": "composer", "p_namespace": "", "p_sep": ":"},
    "pear": {"p_type": "pear", "p_namespace": "", "p_sep": "/"},
    "photon": {"p_type": "rpm", "p_namespace": "photon", "p_sep": "/"},
    "pypi": {"p_type": "pypi", "p_namespace": "", "p_sep": "/"},
    "redhat": {"p_type": "rpm", "p_namespace": "redhat", "p_sep": "/"},
    "ros": {"p_type": "deb", "p_namespace": "ros", "p_sep": "/"},
    "rubygems": {"p_type": "gem", "p_namespace": "", "p_sep": "/"},
    "ubuntu": {"p_type": "deb", "p_namespace": "ubuntu", "p_sep": "/"},
    "yocto": {"p_type": "yocto", "p_namespace": "", "p_sep": "/"},
}


# 1. translate external_namespace to purl_type [and optionally, purl_namespace]
# 2. split external_id into component_id and version:
#     if: external_namespace not in (npmjs, maven) and splt(external_id by id_separator) > 2 segements
#         split external_id by id_separator on first occurence
#             1: component_id
#             2: version
#     else:
#         split external_id by id_separator on last occurence
#             1: component_id
#             2: version
# 3. purl := "pkg:{:purl_type}"
# 4. if purl_namespace:
#     purl += "/{:purl_namespace}"
# 5. if id_separator in component_id:
#     purl += "/" + 1st part of split(component_id by id_separator)
# 6. if id_separator not in component_id:
#         if external_namespace is pypi
#             then purl += "/" + regexp_replace(lower(component_id), '[-_.]+', '-', 'g')
#             else purl += "/{:component_id}"
#         else
#             purl += "/" + 2nd part of split(component_id by id_separator)
# 7. purl += "@" + 1st part of split(regexp_replace(version, '^\d+:', '') by id_separator)
#    append qualifiers if any:
# 8.    purl += "?"
# 9.    if id_separator in version:
#          then purl += "&arch=" + 2nd part of split(version by id_separator)
# 10.   if version matches /^(\d+):/
#         then purl += "&epoch=" + match_group_1
# 11.   if other qualifier:
#         append uri params
# 12. if subpath is known (i.e. golang import subpath)
#     purl += "#{:subpath}"

def calculate_purl(namespace, extid):
    global spdx_origin_map

    if namespace in spdx_origin_map.keys():
        ns_split = extid.split(spdx_origin_map[namespace]['p_sep'])
        if namespace not in ['npmjs', 'maven'] and len(ns_split) > 2:  # 2
            compid, compver = extid.split(spdx_origin_map[namespace]['p_sep'], maxsplit=1)
        elif spdx_origin_map[namespace]['p_sep'] in extid:
            compid, compver = extid.rsplit(spdx_origin_map[namespace]['p_sep'], maxsplit=1)
        else:
            compid, compver = extid, None

        purl = "pkg:" + spdx_origin_map[namespace]['p_type']  # 3

        if spdx_origin_map[namespace]['p_namespace'] != '':  # 4
            purl += "/" + spdx_origin_map[namespace]['p_namespace']

        if spdx_origin_map[namespace]['p_sep'] in compid:  # 5
            purl += '/' + '/'.join(quote(s) for s in compid.split(spdx_origin_map[namespace]['p_sep']))
        else:  # 6
            if namespace == 'pypi':
                purl += '/' + quote(re.sub('[-_.]+', '-', compid.lower()))
            else:
                purl += '/' + quote(compid)

        qual = {}
        if compver:
            if spdx_origin_map[namespace]['p_sep'] in compver:  # 9
                compver, qual['arch'] = compver.split(spdx_origin_map[namespace]['p_sep'])

            purl += '@' + quote(re.sub("^\d+:", '', compver))  # 7

            epoch_m = re.match('^(\d+):', compver)  # 10
            if epoch_m:
                qual['epoch'] = epoch_m[1]

        if qual:
            purl += '?' + '&'.join('='.join([k, quote(v)]) for k, v in qual.items())  # 8

        return purl
    return ''


def get_orig_data(dcomp):
    # Get copyrights, CPE
    copyrights = "NOASSERTION"
    cpe = "NOASSERTION"
    pkg = "NOASSERTION"
    try:
        if 'origins' in dcomp.keys() and len(dcomp['origins']) > 0:
            orig = dcomp['origins'][0]
            if 'externalNamespace' in orig.keys() and 'externalId' in orig.keys():
                pkg = calculate_purl(orig['externalNamespace'], orig['externalId'])

            link = next((item for item in orig['_meta']['links'] if item["rel"] == "component-origin-copyrights"), None)
            thishref = link['href'] + "?limit=100"
            # custom_headers = {'Accept': 'application/vnd.blackducksoftware.copyright-4+json'}
            # resp = hub.execute_get(thishref, custom_headers=custom_headers)
            headers = {
                'accept': "application/vnd.blackducksoftware.copyright-4+json",
            }
            resp = bd.get_json(thishref, headers=headers)
            for copyrt in resp['items']:
                if copyrt['active']:
                    thiscr = copyrt['updatedCopyright'].splitlines()[0].strip()
                    if thiscr not in copyrights:
                        if copyrights == "NOASSERTION":
                            copyrights = thiscr
                        else:
                            copyrights += "\n" + thiscr
        else:
            pass
    # print("	INFO: No copyright data available due to no assigned origin")

    except Exception as exc:
        print("except" + str(exc))

    return copyrights, cpe, pkg


def get_comments(ccomp):
    # Get comments/annotations
    annotations = []
    try:
        hrefs = ccomp['_meta']['links']

        link = next((item for item in hrefs if item["rel"] == "comments"), None)
        if link:
            thishref = link['href']
            # custom_headers = {'Accept': 'application/vnd.blackducksoftware.bill-of-materials-6+json'}
            # resp = hub.execute_get(thishref, custom_headers=custom_headers)
            headers = {
                'accept': "application/vnd.blackducksoftware.bill-of-materials-6+json",
            }
            resp = bd.get_json(thishref, headers=headers)
            mytime = datetime.datetime.now()
            mytime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            for comment in resp['items']:
                annotations.append(
                    {
                        "annotationDate": quote(mytime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
                        "annotationType": "OTHER",
                        "annotator": quote("Person: " + comment['user']['email']),
                        "comment": quote(comment['comment']),
                    }
                )
    except Exception as exc:
        pass
    return annotations


def get_files(fcomp):
    # Get files
    retfile = "NOASSERTION"
    try:
        hrefs = fcomp['_meta']['links']

        link = next((item for item in hrefs if item["rel"] == "matched-files"), None)
        if link:
            thishref = link['href']
            # custom_headers = {'Accept': 'application/vnd.blackducksoftware.bill-of-materials-6+json'}
            # resp = hub.execute_get(thishref, custom_headers=custom_headers)
            headers = {
                'accept': "application/vnd.blackducksoftware.bill-of-materials-6+json",
            }
            resp = bd.get_json(thishref, headers=headers)

            cfile = resp['items']
            if len(cfile) > 0:
                retfile = cfile[0]['filePath']['path']
    except Exception as exc:
        pass
    return retfile


def process_comp(tcomp):
    global output_dict
    global bom_components
    global bom_comp_dict
    global spdx_custom_lics

    cver = tcomp['componentVersion']
    if cver in compdict.keys():
        # ind = compverlist.index(tcomp['componentVersion'])
        bomentry = compdict[cver]
    else:
        bomentry = tcomp

    # for match in bom_components['items']:
    # 	if match['componentVersion'] == comp['componentVersion']:
    # 		bomentry = match
    # 		break

    if cver not in output_dict.keys():
        download_url = "NOASSERTION"

        if args.download_loc:
            openhub_url = next((item for item in bomentry['_meta']['links'] if item["rel"] == "openhub"), None)
            if openhub_url is not None:
                download_url = openhub_get_download(openhub_url['href'])

        copyrights = "NOASSERTION"
        cpe = "NOASSERTION"
        pkg = "NOASSERTION"
        if not args.no_copyrights:
            copyrights, cpe, pkg = get_orig_data(bomentry)

        package_file = "NOASSERTION"
        if not args.no_files:
            package_file = get_files(bomentry)

        desc = 'NOASSERTION'
        if 'description' in tcomp.keys():
            desc = re.sub('[^a-zA-Z.()\d\s\-:]', '', bomentry['description'])

        output_dict[cver] = {}

        annotations = get_comments(bomentry)
        lic_string = get_licenses(bomentry)

        spdxpackage_name = clean_for_spdx(
            "SPDXRef-Package-" + tcomp['componentName'] + "-" + tcomp['componentVersionName'])
        output_dict[cver]['spdxname'] = spdxpackage_name
        output_dict[cver]['spdxentry'] = {
            "SPDXID": quote(spdxpackage_name),
            "name": quote(tcomp['componentName']),
            "versionInfo": quote(tcomp['componentVersionName']),
            "packageFileName": quote(package_file),
            "description": quote(desc),
            "downloadLocation": quote(download_url),
            # PackageChecksum: SHA1: 85ed0817af83a24ad8da68c2b5094de69833983c,
            "licenseConcluded": quote(lic_string),
            "licenseDeclared": quote(lic_string),
            # PackageLicenseComments: <text>Other versions available for a commercial license</text>,
            "filesAnalyzed": False,
            # "ExternalRef: SECURITY cpe23Type {}".format(cpe),
            # "ExternalRef: PACKAGE-MANAGER purl pkg:" + pkg,
            # ExternalRef: PERSISTENT-ID swh swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2,
            # ExternalRef: OTHER LocationRef-acmeforge acmecorp/acmenator/4.1.3-alpha,
            # ExternalRefComment: This is the external ref for Acme,
            "copyrightText": quote(copyrights),
            "annotations": annotations,
        }

        if pkg != '':
            output_dict[cver]['spdxentry']["externalRefs"] = [
                {
                    "referenceLocator": pkg,
                    "referenceCategory": "OTHER",
                }
            ]


def process_children(compverurl, child_url, indenttext):
    global output_dict
    global spdx_custom_lics

    # res = hub.execute_get(child_url)
    # if res is None:
    #     print("Cannot get children")
    #     sys.exit(1)
    res = bd.get_json(child_url)

    children = []
    thismatchtypes = []

    if compverurl not in output_dict.keys():
        output_dict[compverurl] = {}

    # print(res.json())
    for child in res['items']:
        if 'componentName' in child and 'componentVersionName' in child:
            print("{}{}/{}".format(indenttext, child['componentName'], child['componentVersionName']))
            children.append(child['componentVersion'])
            thismatchtypes.append(child['matchTypes'])
        else:
            # No version - skip
            print("{}{}/{} (SKIPPED)".format(indenttext, child['componentName'], '?'))
            continue

        process_comp(child)

        if len(child['_meta']['links']) > 2:
            thisref = [d['href'] for d in child['_meta']['links'] if d['rel'] == 'children']
            process_children(child['componentVersion'], thisref[0], "    " + indenttext)

    if 'children' in output_dict[compverurl].keys():
        output_dict[compverurl]['children'].extend(children)
        output_dict[compverurl]['matchtypes'].extend(thismatchtypes)
    else:
        output_dict[compverurl]['children'] = children
        output_dict[compverurl]['matchtypes'] = thismatchtypes

    return


def add_snippet():
    # "snippets": [{
    # 	"SPDXID": "SPDXRef-Snippet",
    # 	"comment": "This snippet was identified as significant and highlighted in this Apache-2.0 file, when a
    # 	commercial scanner identified it as being derived from file foo.c in package xyz which is licensed under
    # 	GPL-2.0.",
    # 	"copyrightText": "Copyright 2008-2010 John Smith",
    # 	"licenseComments": "The concluded license was taken from package xyz, from which the snippet was copied
    # 	into the current file. The concluded license information was found in the COPYING.txt file in package xyz.",
    # 	"licenseConcluded": "GPL-2.0-only",
    # 	"licenseInfoInSnippets": ["GPL-2.0-only"],
    # 	"name": "from linux kernel",
    # 	"ranges": [{
    # 		"endPointer": {
    # 			"lineNumber": 23,
    # 			"reference": "SPDXRef-DoapSource"
    # 		},
    # 		"startPointer": {
    # 			"lineNumber": 5,
    # 			"reference": "SPDXRef-DoapSource"
    # 		}
    # 	}, {
    # 		"endPointer": {
    # 			"offset": 420,
    # 			"reference": "SPDXRef-DoapSource"
    # 		},
    # 		"startPointer": {
    # 			"offset": 310,
    # 			"reference": "SPDXRef-DoapSource"
    # 		}
    # 	}],
    # 	"snippetFromFile": "SPDXRef-DoapSource"
    # }],
    pass


def report_children(parentverurl, parentpackage, mtypes, children):
    global output_dict
    global spdx
    global processed_list

    for child in children:
        reln = False
        for tchecktype in matchtype_depends_dict.keys():
            if tchecktype in mtypes:
                add_relationship(parentpackage, output_dict[child]['spdxname'], matchtype_depends_dict[tchecktype])
                reln = True
                break
        if not reln:
            for tchecktype in matchtype_contains_dict.keys():
                if tchecktype in mtypes:
                    add_relationship(parentpackage, output_dict[child]['spdxname'],
                                     matchtype_contains_dict[tchecktype])
                    break
        # compver = child['componentVersion']
        processed_list.append(child)

        centry = output_dict[child]
        spdx['packages'].append(centry['spdxentry'])
        if child not in processed_list:
            if 'children' in centry:
                report_children(child, centry['spdxname'], centry['matchtypes'], centry['children'])


def process_project(hcomps, bom):
    global topchildren
    global matchtypes
    global proj_list
    global spdx
    global spdx_custom_lics

    children = []
    childmatchtypes = []

    #
    # Process hierarchical BOM elements
    for hcomp in hcomps:
        if 'componentVersionName' in hcomp:
            print("{}/{}".format(hcomp['componentName'], hcomp['componentVersionName']))
        else:
            print("{}/? - (no version - skipping)".format(hcomp['componentName']))
            continue

        process_comp(hcomp)

        href = [d['href'] for d in hcomp['_meta']['links'] if d['rel'] == 'children']
        if len(href) > 0:
            process_children(hcomp['componentVersion'], href[0], "--> ")

        children.append(hcomp['componentVersion'])
        childmatchtypes.append(hcomp['matchTypes'])

    #
    # Process all entries to find manual entries (not in hierarchical BOM) and sub-projects
    for bom_component in bom:

        # First check if this component is a sub-project
        if bom_component['matchTypes'][0] == "MANUAL_BOM_COMPONENT":
            if 'componentVersionName' not in bom_component.keys():
                print(
                    "INFO: Skipping component {} which has no assigned version".format(bom_component['componentName']))
                continue

            # spdxpackage_name = clean(
            # 	"SPDXRef-Package-" + bom_component['componentName'] + "-" + bom_component['componentVersionName'])

            print(bom_component['componentName'] + "/" + bom_component['componentVersionName'])
            process_comp(bom_component)
            children.append(bom_component['componentVersion'])
            childmatchtypes.append(bom_component['matchTypes'])

            if args.recursive and bom_component['componentName'] in proj_list:
                # sub_project = hub.get_project_by_name(bom_component['componentName'])
                done = False
                params = {
                    'q': "name:" + bom_component['componentName'],
                }
                sub_projects = bd.get_resource('projects', params=params)
                for sub_proj in sub_projects:
                    params = {
                        'q': "versionName:" + bom_component['componentVersionName'],
                    }
                    # sub_version = hub.get_version_by_name(sub_project, bom_component['componentVersionName'])
                    sub_versions = bd.get_resource('versions', parent=sub_proj, params=params)
                    for sub_ver in sub_versions:
                        print("Processing project within project '{}'".format(
                            bom_component['componentName'] + '/' + bom_component['componentVersionName']))
                        done = True
                        # sub_bom_components = hub.get_version_components(sub_version, 5000)
                        # sub_version_url = sub_version['_meta']['href']
                        # sub_hierarchy_url = sub_version_url + "/hierarchical-components?limit=5000"
                        # res = hub.execute_get(sub_hierarchy_url)
                        sub_comps = bd.get_resource('components', parent=sub_ver)
                        sub_hierarchical_bom = bd.get_resource('hierarchical-components', parent=version)

                        # subprojchildren, subprojmatchtypes = process_project(
                        #     res.json()['items'], sub_bom_components['items'])
                        subprojchildren, subprojmatchtypes = process_project(sub_hierarchical_bom, sub_comps)
                        if bom_component['componentVersion'] in output_dict.keys() and \
                                'children' in output_dict[bom_component['componentVersion']]:
                            output_dict[bom_component['componentVersion']]['children'].extend(subprojchildren)
                            output_dict[bom_component['componentVersion']]['matchtypes'].extend(subprojmatchtypes)
                        else:
                            output_dict[bom_component['componentVersion']]['children'] = subprojchildren
                            output_dict[bom_component['componentVersion']]['matchtypes'] = subprojmatchtypes

    return children, childmatchtypes


def add_relationship(parent, child, reln):
    global spdx

    mydict = {
        "spdxElementId": quote(parent),
        "relationshipType": quote(reln),
        "relatedSpdxElement": quote(child)
    }
    spdx['relationships'].append(mydict)


def check_params():
    global args

    if args.version:
        print("Script version: " + script_version)
        sys.exit(0)

    if args.basic:
        args.download_loc = False
        args.no_copyrights = True
        args.no_files = True
    if args.output == "":
        args.output = clean_for_spdx(args.project_name + "-" + args.project_version) + ".json"

    if args.output and os.path.exists(args.output):
        backup_file(args.output)


def check_projver(args):
    params = {
        'q': "name:" + args.project_name,
        'sort': 'name',
    }
    # project = hub.get_project_by_name(args.project_name)
    projects = bd.get_resource('projects', params=params, items=False)

    if projects['totalCount'] == 0:
        print("Project '{}' does not exist".format(args.project_name))
        print('Available projects:')
        projects = bd.get_resource('projects')
        for proj in projects:
            print(proj['name'])
        sys.exit(2)

    projects = bd.get_resource('projects', params=params)
    # version = hub.get_version_by_name(project, args.project_version)
    for proj in projects:
        versions = bd.get_resource('versions', parent=proj, params=params)
        for ver in versions:
            if ver['versionName'] == args.project_version:
                return proj, ver
    print("Version '{}' does not exist in project '{}'".format(args.project_name, args.project_version))
    sys.exit(2)


print("BLACK DUCK SPDX EXPORT SCRIPT VERSION {}\n".format(script_version))

check_params()

project, version = check_projver(args)
print("Working on project '{}' version '{}'\n".format(project['name'], version['versionName']))

if args.recursive:
    proj_list = get_all_projects()

bom_components = bd.get_resource('components', parent=version)
# compverlist = []
bom_comp_dict = {}
for comp in bom_components:
    compver = comp['componentVersion']
    # compverlist.append(compver)
    bom_comp_dict[compver] = comp

# process_components(bom_components)

#######################################################################################################################
#
# Get the BOM component entries
# version_url = version['_meta']['href']
# hierarchy_url = version_url + "/hierarchical-components?limit=5000"
# hierarchy = hub.execute_get(hierarchy_url)
# if hierarchy.status_code != 200:
#     logging.error("Failed to retrieve hierarchy, status code: {}".format(hierarchy.status_code))
#     exit()

output_dict = dict()
# output_compsdict entries look like this:
# 'spdx': SPDX record
# 'spdxname': SPDX record name
# 'children': List of projver URLs which are children
# 'matchtypes': List of lists of scan match types for children

output_dict['TOPLEVEL'] = {}
output_dict['TOPLEVEL']['children'] = []
spdx_custom_lics = []

if 'hierarchical-components' in bd.list_resources(version):
    hierarchical_bom = bd.get_resource('hierarchical-components', parent=version)

    print('Getting Component Hierarchy:')
    topchildren, matchtypes = process_project(hierarchical_bom, bom_components)

    output_dict['TOPLEVEL']['children'] = topchildren
    output_dict['TOPLEVEL']['matchtypes'] = matchtypes

toppackage = clean_for_spdx("SPDXRef-Package-" + project['name'] + "-" + version['versionName'])

# Define TOP Document entries
spdx["SPDXID"] = "SPDXRef-DOCUMENT"
spdx["spdxVersion"] = "SPDX-2.2"
spdx["creationInfo"] = {
    "created": quote(version['createdAt'].split('.')[0] + 'Z'),
    "creators": ["Tool: Black Duck SPDX export script https://gihub.com/matthewb66/bd_export_spdx"],
    "licenseListVersion": "3.9",
}
if 'description' in project.keys():
    spdx["creationInfo"]["comment"] = quote(project['description'])
spdx["name"] = quote(project['name'] + '/' + version['versionName'])
spdx["dataLicense"] = "CC0-1.0"
# spdx["DocumentNamespace"] = '"' + version['_meta']['href'] + '"'
spdx["documentDescribes"] = [toppackage]
add_relationship("SPDXRef-DOCUMENT", toppackage, "DESCRIBES")


# Add top package for project version

projpkg = {
    "SPDXID": quote(toppackage),
    "name": quote(project['name']),
    "versionInfo": quote(version['versionName']),
    # "packageFileName":  quote(package_file),
    # "downloadLocation": quote(download_url),
    # PackageChecksum: SHA1: 85ed0817af83a24ad8da68c2b5094de69833983c,
    # "licenseConcluded": quote(lic_string),
    # "licenseDeclared": quote(lic_string),
    # PackageLicenseComments: <text>Other versions available for a commercial license</text>,
    # "filesAnalyzed": False,
    # "ExternalRef: SECURITY cpe23Type {}".format(cpe),
    # "ExternalRef: PACKAGE-MANAGER purl pkg:" + pkg,
    # ExternalRef: PERSISTENT-ID swh swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2,
    # ExternalRef: OTHER LocationRef-acmeforge acmecorp/acmenator/4.1.3-alpha,
    # ExternalRefComment: This is the external ref for Acme,
    # "copyrightText": quote(copyrights),
    # annotations,
}
if 'description' in project.keys():
    projpkg["description"] = quote(project['description'])
if 'license' in version.keys():
    projpkg["licenseDeclared"] = version['license']['licenseDisplay']
spdx['packages'].append(projpkg)

#
# Walk the compsdict tree to report SPDX entities
print('\nProcessing component tree ...', end='')
processed_list = []
index = 0
for compver in output_dict['TOPLEVEL']['children']:
    matchtypes = output_dict['TOPLEVEL']['matchtypes'][index]

    rel = False
    for checktype in matchtype_depends_dict.keys():
        if checktype in matchtypes:
            add_relationship(toppackage, output_dict[compver]['spdxname'], matchtype_depends_dict[checktype])
            rel = True
            break
    if not rel:
        for checktype in matchtype_contains_dict.keys():
            if checktype in matchtypes:
                add_relationship(toppackage, output_dict[compver]['spdxname'], matchtype_contains_dict[checktype])
                break

    processed_list.append(compver)

    compentry = output_dict[compver]
    spdx['packages'].append(compentry['spdxentry'])
    # if compver not in processed_list:
    if 'children' in compentry and len(compentry['children']) > 0:
        report_children(compver, compentry['spdxname'], compentry['matchtypes'], compentry['children'])

    index += 1
#
# if len(spdx_custom_lics_text) > 0:
# 	spdx.append('## Custom Licenses')
# 	spdx += spdx_custom_lics_text

print("Done\n\nWriting SPDX output file {} ... ".format(args.output), end='')

try:
    with open(args.output, 'w') as outfile:
        json.dump(spdx, outfile)

except Exception as e:
    print('ERROR: Unable to create output report file \n' + str(e))
    sys.exit(3)

print("Done")
