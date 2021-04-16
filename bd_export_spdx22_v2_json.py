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

from blackduck.HubRestApi import HubInstance

script_version = "0.21 Beta"

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', stream=sys.stderr, level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

hub = HubInstance()

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


def list_projects(project_string):
	print("Available projects matching '{}':".format(project_string))
	projs = hub.get_projects(parameters={"q": "name:{}".format(project_string)})
	for proj in projs['items']:
		print(" - " + proj['name'])


def get_all_projects():
	projs = hub.get_projects(5000)
	projlist = []
	for proj in projs['items']:
		projlist.append(proj['name'])
	return projlist


def list_versions(proj):
	print("Available versions:")
	vers = hub.get_project_versions(proj, parameters={})
	for ver in vers['items']:
		print(" - " + ver['versionName'])


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
					lic_url = hub.get_apibase() + '/licenses/' + lic_ref + '/text'
					custom_headers = {'Accept': 'text/plain'}
					resp = hub.execute_get(lic_url, custom_headers=custom_headers)
					lic_text = resp.content.decode("utf-8")
					if thislic not in spdx_custom_lics:
						spdx["hasExtractedLicensingInfos"].append(
							{
								'licenseID': quote(thislic),
								'extractedText': quote(lic_text),
							}
						)
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


def calculate_purl(namespace, extid):
	global spdx_origin_map

	if namespace in spdx_origin_map.keys():
		ns_split = extid.split(spdx_origin_map[namespace]['p_sep'])
		if namespace not in ['npmjs', 'maven'] and len(ns_split) > 2:
			pos = extid.find(spdx_origin_map[namespace]['p_sep'])
		else:
			pos = extid.rfind(spdx_origin_map[namespace]['p_sep'])
		compid = extid[:pos]
		compver = extid[pos + 1:]
		purl = "pkg:" + spdx_origin_map[namespace]['p_type']
		if spdx_origin_map[namespace]['p_namespace'] != '':
			purl += "/" + spdx_origin_map[namespace]['p_namespace']
		sep = compid.find(spdx_origin_map[namespace]['p_sep'])
		if sep >= 0:
			purl += '/' + compid[:pos]
			purl += '/' + compid[pos + 1:]
		else:
			if namespace == 'pypi':
				purl += '/' + re.sub('[-_.]+', '-', compid.lower())
			else:
				purl += '/' + compid

		purl += '@' + re.sub('^\d+:', '', compver)

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
			custom_headers = {'Accept': 'application/vnd.blackducksoftware.copyright-4+json'}
			resp = hub.execute_get(thishref, custom_headers=custom_headers)
			for copyrt in resp.json()['items']:
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
			custom_headers = {'Accept': 'application/vnd.blackducksoftware.bill-of-materials-6+json'}
			resp = hub.execute_get(thishref, custom_headers=custom_headers)
			mytime = datetime.datetime.now()
			mytime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
			for comment in resp.json()['items']:
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
			custom_headers = {'Accept': 'application/vnd.blackducksoftware.bill-of-materials-6+json'}
			resp = hub.execute_get(thishref, custom_headers=custom_headers)
			cfile = resp.json()['items']
			if len(cfile) > 0:
				retfile = cfile[0]['filePath']['path']
	except Exception as exc:
		pass
	return retfile


def process_comp(tcomp):
	global compsdict, bom_components, compverlist

	bomentry = None
	if tcomp['componentVersion'] in compverlist:
		ind = compverlist.index(tcomp['componentVersion'])
		bomentry = bom_components['items'][ind]

	# for match in bom_components['items']:
	# 	if match['componentVersion'] == comp['componentVersion']:
	# 		bomentry = match
	# 		break

	if bomentry is None:
		bomentry = tcomp

	cver = tcomp['componentVersion']
	if cver not in compsdict.keys():
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

		compsdict[cver] = {}

		annotations = get_comments(bomentry)
		lic_string = get_licenses(bomentry)

		spdxpackage_name = clean_for_spdx(
			"SPDXRef-Package-" + tcomp['componentName'] + "-" + tcomp['componentVersionName'])
		compsdict[cver]['spdxname'] = spdxpackage_name
		compsdict[cver]['spdxentry'] = {
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
			compsdict[cver]['spdxentry']["externalRefs"] = [
				{
					"referenceLocator": pkg,
					"referenceCategory": "OTHER",
				}
			]


def process_children(compverurl, child_url, indenttext):
	global compsdict

	res = hub.execute_get(child_url)
	if res is None:
		print("Cannot get children")
		sys.exit(1)

	children = []
	thismatchtypes = []

	if compverurl not in compsdict.keys():
		compsdict[compverurl] = {}

	# print(res.json())
	for child in res.json()['items']:
		if 'componentVersionName' in child and 'componentVersionName' in child:
			print("{}{}/{}".format(indenttext, child['componentName'], child['componentVersionName']))
			children.append(child['componentVersion'])
			thismatchtypes.append(child['matchTypes'])
		else:
			# No version - skip
			print("{}{}/{}".format(indenttext, child['componentName'], '?'))
			continue

		process_comp(child)

		if len(child['_meta']['links']) > 2:
			thisref = [d['href'] for d in child['_meta']['links'] if d['rel'] == 'children']
			process_children(child['componentVersion'], thisref[0], "    " + indenttext)

	if 'children' in compsdict[compverurl].keys():
		compsdict[compverurl]['children'].append(children)
		compsdict[compverurl]['matchtypes'].append(thismatchtypes)
	else:
		compsdict[compverurl]['children'] = children
		compsdict[compverurl]['matchtypes'] = thismatchtypes

	return


def add_snippet():
	# "snippets": [{
	# 	"SPDXID": "SPDXRef-Snippet",
	# 	"comment": "This snippet was identified as significant and highlighted in this Apache-2.0 file, when a commercial scanner identified it as being derived from file foo.c in package xyz which is licensed under GPL-2.0.",
	# 	"copyrightText": "Copyright 2008-2010 John Smith",
	# 	"licenseComments": "The concluded license was taken from package xyz, from which the snippet was copied into the current file. The concluded license information was found in the COPYING.txt file in package xyz.",
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
	global compsdict
	global spdx

	for child in children:
		if child == parentverurl:
			continue
		reln = False
		for tchecktype in matchtype_depends_dict.keys():
			if tchecktype in mtypes:
				add_relationship(parentpackage, compsdict[child]['spdxname'], matchtype_depends_dict[tchecktype])
				reln = True
				break
		if not reln:
			for tchecktype in matchtype_contains_dict.keys():
				if tchecktype in mtypes:
					add_relationship(parentpackage, compsdict[child]['spdxname'], matchtype_contains_dict[tchecktype])
					break

		centry = compsdict[child]
		spdx['packages'].append(centry['spdxentry'])
		if 'children' in centry:
			report_children(child, centry['spdxname'], centry['matchtypes'], centry['children'])


if args.version:
	print("Script version: " + script_version)
	sys.exit(0)

if args.basic:
	args.download_loc = False
	args.no_copyrights = True
	args.no_files = True
if args.output == "":
	args.output = clean_for_spdx(args.project_name + "-" + args.project_version) + ".json"

print("BLACK DUCK SPDX EXPORT SCRIPT VERSION {}\n".format(script_version))

project = hub.get_project_by_name(args.project_name)
if project is None:
	print("Project '{}' does not exist".format(args.project_name))
	list_projects(args.project_name)
	sys.exit(2)

version = hub.get_version_by_name(project, args.project_version)
if version is None:
	print("Version '{}' does not exist".format(args.project_version))
	list_versions(project)
	sys.exit(2)
else:
	print("Working on project '{}' version '{}'\n".format(args.project_name, args.project_version))

if args.output and os.path.exists(args.output):
	backup_file(args.output)

if args.recursive:
	proj_list = get_all_projects()

bom_components = hub.get_version_components(version, 5000)
compverlist = []
for comp in bom_components['items']:
	compver = comp['componentVersion']
	compverlist.append(compver)

# process_components(bom_components)

#######################################################################################################################
#
# Get the BOM component entries
version_url = version['_meta']['href']
hierarchy_url = version_url + "/hierarchical-components?limit=5000"
hierarchy = hub.execute_get(hierarchy_url)
if hierarchy.status_code != 200:
	logging.error("Failed to retrieve hierarchy, status code: {}".format(hierarchy.status_code))
	exit()

# print(json.dumps(hierarchy.json(), indent=4, sort_keys=True))

compsdict = dict()
# compsdict entries look like this:
# 'spdx': SPDX record
# 'spdxname': SPDX record name
# 'children': List of projver URLs which are children
# 'matchtypes': List of lists of scan match types for children

compsdict['TOPLEVEL'] = {}
compsdict['TOPLEVEL']['children'] = []


def process_project(hcomps, bom):
	global topchildren
	global matchtypes
	global proj_list
	global spdx

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
				sub_project = hub.get_project_by_name(bom_component['componentName'])
				if sub_project != "" and sub_project is not None:
					sub_version = hub.get_version_by_name(sub_project, bom_component['componentVersionName'])
					if sub_version != "" and sub_version is not None:
						print("Processing project within project '{}'".format(
							bom_component['componentName'] + '/' + bom_component['componentVersionName']))
						sub_bom_components = hub.get_version_components(sub_version, 5000)
						sub_version_url = sub_version['_meta']['href']
						sub_hierarchy_url = sub_version_url + "/hierarchical-components?limit=5000"
						res = hub.execute_get(sub_hierarchy_url)
						if res.status_code != 200:
							logging.error(
								"Failed to retrieve hierarchy, status code: {}".format(res.status_code))
							sys.exit(3)

						subprojchildren, subprojmatchtypes = process_project(
							res.json()['items'], sub_bom_components['items'])
						compsdict[bom_component['componentVersion']]['children'] = subprojchildren
						compsdict[bom_component['componentVersion']]['matchtypes'] = subprojmatchtypes

	return children, childmatchtypes


def add_relationship(parent, child, reln):
	global spdx

	spdx['relationships'].append(
		{
			"spdxElementId": quote(parent),
			"relatedSpdxElement": quote(child),
			"relationshipType": quote(reln)
		}
	)


topchildren, matchtypes = process_project(hierarchy.json()['items'], bom_components['items'])

compsdict['TOPLEVEL']['children'] = topchildren
compsdict['TOPLEVEL']['matchtypes'] = matchtypes

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
add_relationship("Relationship: SPDXRef-DOCUMENT", toppackage, "DESCRIBES")

spdx_custom_lics = []

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
index = 0
for compver in compsdict['TOPLEVEL']['children']:
	matchtypes = compsdict['TOPLEVEL']['matchtypes'][index]
	rel = False
	for checktype in matchtype_depends_dict.keys():
		if checktype in matchtypes:
			add_relationship(toppackage, compsdict[compver]['spdxname'], matchtype_depends_dict[checktype])
			rel = True
			break
	if not rel:
		for checktype in matchtype_contains_dict.keys():
			if checktype in matchtypes:
				add_relationship(toppackage, compsdict[compver]['spdxname'], matchtype_contains_dict[checktype])
				break

	compentry = compsdict[compver]
	spdx['packages'].append(compentry['spdxentry'])
	if 'children' in compentry and len(compentry['children']) > 0:
		report_children(compver, compentry['spdxname'], compentry['matchtypes'], compentry['children'])

	index += 1
#
# if len(spdx_custom_lics_text) > 0:
# 	spdx.append('## Custom Licenses')
# 	spdx += spdx_custom_lics_text

print("\nWriting SPDX output file {} ... ".format(args.output), end='')

try:
	with open(args.output, 'w') as outfile:
		json.dump(spdx, outfile)

except Exception as e:
	print('ERROR: Unable to create output report file \n' + str(e))
	sys.exit(3)

print("Done")
