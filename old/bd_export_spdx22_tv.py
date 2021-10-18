#!/usr/bin/env python
import argparse
# import json
import logging
import sys
import datetime
import os
import re
from lxml import html
import requests
# from zipfile import ZipFile

from blackduck.HubRestApi import HubInstance

script_version = "0.16 Beta"

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', stream=sys.stderr, level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def clean(name):
	remove_chars = [';', ':', '!', "*", "(", ")", "/", ","]
	for i in remove_chars:
		name = name.replace(i, '')
	replace_chars = [' ', '.']
	for i in replace_chars:
		name = name.replace(i, '-')
	return name


def list_projects(project_string):
	print("Available projects matching '{}':".format(project_string))
	projs = hub.get_projects(parameters={"q": "name:{}".format(project_string)})
	for proj in projs['items']:
		print(" - " + proj['name'])


def get_all_projects():
	projs = hub.get_projects()
	projlist = []
	for proj in projs['items']:
		projlist.append(proj['name'])
	return projlist


def list_versions():
	print("Available versions:")
	vers = hub.get_project_versions(project, parameters={})
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


def get_licenses(comp):
	global spdx_custom_lics, spdx_custom_lics_text

	# Get licenses
	lic_string = "NOASSERTION"
	quotes = False
	if 'licenses' in comp.keys():
		proc_item = comp['licenses']

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
					thislic = 'LicenseRef-' + clean(lic['licenseDisplay'])
					lic_ref = lic['license'].split("/")[-1]
					lic_url = hub.get_apibase() + '/licenses/' + lic_ref + '/text'
					custom_headers = {'Accept': 'text/plain'}
					resp = hub.execute_get(lic_url, custom_headers=custom_headers)
					lic_text = resp.content.decode("utf-8")
					if thislic not in spdx_custom_lics:
						spdx_custom_lics_text += ['', 'LicenseID: ' + thislic,
												  'ExtractedText: <text>' + lic_text + '</text>']
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


def get_orig_data(comp):
	# Get copyrights, CPE
	copyrights = "NOASSERTION"
	cpe = "NOASSERTION"
	pkg = "NOASSERTION"
	try:
		if 'origins' in comp.keys() and len(comp['origins']) > 0:
			orig = comp['origins'][0]
			if 'externalNamespace' in orig.keys() and 'externalId' in orig.keys():
				thisid = orig['externalId'].split(':')
				if len(thisid) < 2:
					# cpe = "cpe:2.3:a:{}:{}:*:*:*:*:*:*".format(orig['externalNamespace'], orig['externalId'])
					pkg = "{}/{}".format(orig['externalNamespace'], thisid[0])
				elif len(thisid) == 2:
					# Special case for github
					# cpe = "cpe:2.3:a:{}:{}:*:*:*:*:*:*".format(orig['externalNamespace'], orig['externalId'])
					pkg = "{}/{}@{}".format(orig['externalNamespace'], thisid[0], thisid[1])
				elif len(thisid) == 3:
					# cpe = "cpe:2.3:a:{}:*:*:*:*:*:*".format(orig['externalId'])
					pkg = "{}/{}@{}".format(thisid[0], thisid[1], thisid[2])
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
			print("	INFO: No copyright data available due to no assigned origin")
	except Exception as exc:
		print("except" + str(exc))

	if copyrights != 'NOASSERTION':
		copyrights = '<text>' + copyrights + '</text>'

	return copyrights, cpe, pkg


def get_comments(comp):
	# Get comments/annotations
	annotations = ""
	try:
		hrefs = comp['_meta']['links']

		link = next((item for item in hrefs if item["rel"] == "comments"), None)
		if link:
			thishref = link['href']
			custom_headers = {'Accept': 'application/vnd.blackducksoftware.bill-of-materials-6+json'}
			resp = hub.execute_get(thishref, custom_headers=custom_headers)
			mytime = datetime.datetime.now()
			mytime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
			for comment in resp.json()['items']:
				annotations += "AnnotationDate: " + mytime.strftime("%Y-%m-%dT%H:%M:%S.%fZ") + "\n" + \
							   "AnnotationType: OTHER\n" + \
							   "Annotator: Person: " + comment['user']['email'] + "\n" + \
							   "AnnotationComment :" + comment['comment'] + "\n"
		# "SPDXREF: " + spdxpackage_name + "\n"
	except Exception as exc:
		pass
	return annotations


def get_files(comp):
	# Get files
	retfile = "NOASSERTION"
	try:
		hrefs = comp['_meta']['links']

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


def process_comp(comp):
	global output_dict, bom_components

	bomentry = None
	for match in bom_components['items']:
		if match['componentVersion'] == comp['componentVersion']:
			bomentry = match
			break

	if bomentry is None:
		bomentry = comp

	cver = comp['componentVersion']
	if cver not in compsdict.keys():
		openhub_url = next((item for item in bomentry['_meta']['links'] if item["rel"] == "openhub"), None)
		download_url = "NOASSERTION"
		if openhub_url is not None and not args.no_downloads:
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
		if 'description' in comp.keys():
			desc = '<text>' + re.sub('[^a-zA-Z.()\d\s\-:]', '', bomentry['description']) + '</text>'

		compsdict[cver] = {}

		annotations = get_comments(bomentry)
		lic_string = get_licenses(bomentry)

		spdxpackage_name = clean(
			"SPDXRef-Package-" + comp['componentName'] + "-" + comp['componentVersionName'])
		compsdict[cver]['spdxname'] = spdxpackage_name
		compsdict[cver]['spdx'] = [
			'',
			"## Black Duck project component",
			"PackageName: " + comp['componentName'],
			"SPDXID: " + spdxpackage_name,
			"PackageVersion: " + comp['componentVersionName'],
			"PackageFileName: " + package_file,
			"PackageDescription: " + desc,
			"PackageDownloadLocation: " + download_url,
			# PackageChecksum: SHA1: 85ed0817af83a24ad8da68c2b5094de69833983c,
			"PackageLicenseConcluded: " + lic_string,
			"PackageLicenseDeclared: " + lic_string,
			# PackageLicenseComments: <text>Other versions available for a commercial license</text>,
			"FilesAnalyzed: false",
			"ExternalRef: SECURITY cpe23Type {}".format(cpe),
			"ExternalRef: PACKAGE-MANAGER purl pkg:" + pkg,
			# ExternalRef: PERSISTENT-ID swh swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2,
			# ExternalRef: OTHER LocationRef-acmeforge acmecorp/acmenator/4.1.3-alpha,
			# ExternalRefComment: This is the external ref for Acme,
			"PackageCopyrightText: " + copyrights,
			# annotations,
		]


def process_children(compverurl, child_url, indenttext):
	global output_dict

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


def report_children(parentpackage, mtypes, children):
	global output_dict, spdx_body

	parentrels = []
	ind = 0
	for child in children:
		for mtype in mtypes[ind]:
			if mtype in matchtype_dict.keys():
				parentrels.append("Relationship: " + parentpackage + " " + matchtype_dict[mtype] + " " +
								  compsdict[child]['spdxname'])
				break

		centry = compsdict[child]
		spdx_body += centry['spdx']
		if 'children' in centry:
			spdx_body += report_children(centry['spdxname'], centry['matchtypes'],
										 centry['children'])

	ind += 1

	return parentrels


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

matchtype_dict = {
	"FILE_DEPENDENCY_DIRECT": "DEPENDS_ON",
	"FILE_DEPENDENCY_TRANSITIVE": "DEPENDS_ON",
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
	'alpine': '',
	'alt_linux': '',
	'anaconda': '',
	'android': '',
	'android_sdk': '',
	'apache_software': '',
	'arch_linux': '',
	'automotive_linux': '',
	'bitbucket': '',
	'bower': '',
	'centos': '',
	'clearlinux': '',
	'cocoapods': '',
	'codeplex': '',
	'codeplex_group': '',
	'conan': '',
	'cpan': '',
	'cpe': '',
	'cran': '',
	'crates': '',
	'dart': '',
	'debian': '',
	'eclipse': '',
	'efisbot': '',
	'fedora': '',
	'freedesktop_org': '',
	'gitcafe': '',
	'github': '',
	'github_gist': '',
	'gitlab': '',
	'gitorious': '',
	'gnu': '',
	'golang': '',
	'googlecode': '',
	'hackage': '',
	'hex': '',
	'java_net': '',
	'kb_classic': '',
	'kde_org': '',
	'launchpad': '',
	'long_tail': '',
	'maven': '',
	'mongodb': '',
	'npmjs': '',
	'nuget': '',
	'openembedded': '',
	'openjdk': '',
	'opensuse': '',
	'oracle_linux': '',
	'packagist': '',
	'pear': '',
	'photon': '',
	'protecode_sc': '',
	'pypi': '',
	'raspberry_pi': '',
	'redhat': '',
	'ros': '',
	'rubyforge': '',
	'rubygems': '',
	'runtime': '',
	'sourceforge': '',
	'sourceforge_jp': '',
	'tianocore': '',
	'ubuntu': '',
	'yocto': '',
}

parser = argparse.ArgumentParser(description='"Export SPDX for the given project and version"', prog='export_spdx.py')
parser.add_argument("project_name", type=str, help='Black Duck project name')
parser.add_argument("project_version", type=str, help='Black Duck version name')
parser.add_argument("-v", "--version", help="Print script version and exit", action='store_true')
parser.add_argument("-o", "--output",
					type=str,
					help="Output SPDX file name (SPDX tag format) - default '<proj>-<ver>.spdx'", default="")
parser.add_argument("-r", "--recursive", help="Scan sub-projects within projects (default = false)",
					action='store_true')
parser.add_argument("--no_downloads",
					help='''Do not identify component download link extracted from Openhub 
					(speeds up processing - default=false)''',
					action='store_true')
parser.add_argument("--no_copyrights",
					help="Do not export copyright data for components (speeds up processing - default=false)",
					action='store_true')
parser.add_argument("--no_files",
					help="Do not export file data for components (speeds up processing - default=false)",
					action='store_true')
parser.add_argument("-b", "--basic",
					help='''Do not export copyright, download link  or package file data (speeds up processing - 
					same as using "--no_downloads --no_copyrights --no_files")''',
					action='store_true')

args = parser.parse_args()

if args.version:
	print("Script version: " + script_version)
	sys.exit(0)

if args.basic:
	args.no_downloads = True
	args.no_copyrights = True
	args.no_files = True
if args.output == "":
	args.output = clean(args.project_name) + "-" + clean(args.project_version) + ".spdx"

print("BLACK DUCK SPDX EXPORT SCRIPT VERSION {}\n".format(script_version))

hub = HubInstance()

project = hub.get_project_by_name(args.project_name)
if project is None:
	print("Project '{}' does not exist".format(args.project_name))
	list_projects(args.project_name)
	sys.exit(2)

version = hub.get_version_by_name(project, args.project_version)
if version is None:
	print("Version '{}' does not exist".format(args.project_version))
	list_versions()
	sys.exit(2)
else:
	print("Working on project '{}' version '{}'\n".format(args.project_name, args.project_version))

if args.output and os.path.exists(args.output):
	backup_file(args.output)

if args.recursive:
	proj_list = get_all_projects()

bom_components = hub.get_version_components(version)

try:
	spdx = [
		"SPDXVersion: SPDX-2.2",
		"DataLicense: CC0-1.0",
		"DocumentNamespace: " + version['_meta']['href'],
		"DocumentName: " + project['name'] + "/" + version['versionName']
	]

	if 'description' in project.keys():
		spdx.append("DocumentComment: <text>" + project['description'] + "</text>")

	spdx += [
		"SPDXID: SPDXRef-DOCUMENT",
		"## Creation Information",
		"Creator: Tool: Black Duck SPDX export script https://gihub.com/matthewb66/bd_export_spdx",
		"Creator: Person: " + version['createdBy'],
		"Created: " + version['createdAt'].split('.')[0] + 'Z',
		"LicenseListVersion: 3.9",
		"## Relationships"
	]

except Exception as e:
	print('ERROR: Unable to create spdx header\n' + str(e))
	sys.exit(2)

packages = []
spdx_custom_lics_text = []
spdx_custom_lics = []

# process_components(bom_components)

#######################################################################################################################
#
# Get the BOM component entries
version_url = version['_meta']['href']
# https://hubeval39.blackducksoftware.com/api/projects/22631213-fbd4-4daa-99ec-53d0b4f3889f/versions/d2af4a7a-6cdf-4a02-8604-6ff34578dd89/hierarchical-components
hierarchy_url = version_url + "/hierarchical-components?limit=1000"
hierarchy = hub.execute_get(hierarchy_url)
if hierarchy.status_code != 200:
	logging.error("Failed to retrieve hierarchy, status code: {}".format(hierarchy.status_code))
	exit()

# print(json.dumps(hierarchy.json(), indent=4, sort_keys=True))

output_dict = dict()
output_dict['TOPLEVEL'] = {}
output_dict['TOPLEVEL']['children'] = []

topchildren = []
matchtypes = []
count = 0  # DEBUG
for component in hierarchy.json()['items']:
	output = ""
	if 'componentVersionName' in component:
		print("{}/{}".format(component['componentName'], component['componentVersionName']))
	else:
		print("{}/?".format(component['componentName']))
		continue

	process_comp(component)

	href = [d['href'] for d in component['_meta']['links'] if d['rel'] == 'children']
	if len(href) > 0:
		process_children(component['componentVersion'], href[0], "--> ")

	topchildren.append(component['componentVersion'])
	matchtypes.append(component['matchTypes'])
	count += 1
	# if count > 5:  # DEBUG
	# 	break

output_dict['TOPLEVEL']['children'] = topchildren
output_dict['TOPLEVEL']['matchtypes'] = matchtypes

spdx_body = []

toppackage = clean("SPDXRef-Package-" + project['name'] + "-" + version['versionName'])
spdx.append("Relationship: SPDXRef-DOCUMENT DESCRIBES " + toppackage)
spdx.append('')

spdx += [
	"## Black Duck project",
	"PackageName: " + project['name'],
	"SPDXID: " + toppackage,
	"PackageVersion: " + version['versionName'],
	# "PackageFileName: " + package_file,
	# "PackageDescription: " + desc,
	# "PackageDownloadLocation: " + download_url,
	# PackageChecksum: SHA1: 85ed0817af83a24ad8da68c2b5094de69833983c
	# "PackageLicenseConcluded: " + lic_string,
	# "PackageLicenseDeclared: " + lic_string,
	# PackageLicenseComments: <text>Other versions available for a commercial license</text>
	# FilesAnalyzed: false
	# "ExternalRef: SECURITY cpe23Type {}".format(cpe),
	# "ExternalRef: PACKAGE-MANAGER purl pkg:" + pkg,
	# ExternalRef: PERSISTENT-ID swh swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2
	# ExternalRef: OTHER LocationRef-acmeforge acmecorp/acmenator/4.1.3-alpha
	# ExternalRefComment: This is the external ref for Acme
	# "PackageCopyrightText: " + copyrights,
	# annotations,
]

index = 0
for compver in output_dict['TOPLEVEL']['children']:
	matchtypes = output_dict['TOPLEVEL']['matchtypes'][index]
	for matchtype in matchtypes:
		if matchtype in matchtype_dict.keys():
			spdx.append("Relationship: " + toppackage + " " + matchtype_dict[matchtype] + " " +
						output_dict[compver]['spdxname'])
			break

	compentry = output_dict[compver]
	spdx_body += compentry['spdx']
	if 'children' in compentry and len(compentry['children']) > 0:
		spdx_body += report_children(compentry['spdxname'], compentry['matchtypes'],
									 compentry['children'])

	index += 1

spdx.append('')
spdx = spdx + spdx_body

if len(spdx_custom_lics_text) > 0:
	spdx.append('')
	spdx.append('## Custom Licenses')
	spdx += spdx_custom_lics_text

print("\nWriting SPDX output file {} ... ".format(args.output), end='')

try:
	f = open(args.output, "a")

	for line in spdx:
		f.write(line + "\n")
	f.close()

except Exception as e:
	print('ERROR: Unable to create output report file \n' + str(e))
	sys.exit(3)

print("Done")
