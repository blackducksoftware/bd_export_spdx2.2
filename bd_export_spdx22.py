#!/usr/bin/env python
script_version = "0.1 beta"

import argparse
import json
import logging
import sys, time, datetime, os
import re
from lxml import html
import requests
# from zipfile import ZipFile

from blackduck.HubRestApi import HubInstance

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', stream=sys.stderr, level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

usage_dict = {
"SOURCE_CODE": "CONTAINS",
"STATICALLY_LINKED": "STATIC_LINK",
"DYNAMICALLY_LINKED": "DYNAMIC_LINK",
"SEPARATE_WORK": "OTHER",
"MERELY_AGGREGATED": "OTHER",
"IMPLEMENTATION_OF_STANDARD": "OTHER",
"PREREQUISITE": "HAS_PREREQUISITE",
"DEV_TOOL_EXCLUDED": "DEV_TOOL_OF" }

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
'wxWindows': 'NOASSERTION'}

parser = argparse.ArgumentParser(description='"Export SPDX for the given project and version"', prog='export_spdx.py')
parser.add_argument("project_name", type=str, help='Black Duck project name')
parser.add_argument("project_version", type=str, help='Black Duck version name')
parser.add_argument("-v", "--version", help="Print script version and exit",action='store_true')
parser.add_argument("-o", "--output", type=str, help="Output SPDX file name (SPDX tag format) - default '<proj>-<ver>.spdx'", default="")
parser.add_argument("-r", "--recursive", help="Scan sub-projects within projects (default = false)",action='store_true')
parser.add_argument("--no_downloads", help="Do not identify component download link extracted from Openhub (speeds up processing - default=false)",action='store_true')
parser.add_argument("--no_copyrights", help="Do not export copyright data for components (speeds up processing - default=false)",action='store_true')
parser.add_argument("--no_files", help="Do not export file data for components (speeds up processing - default=false)",action='store_true')
parser.add_argument("-b", "--basic", help="Do not export copyright, download link  or package file data (speeds up processing - same as using '--no_downloads --no_copyrights --no_files')",action='store_true')

args = parser.parse_args()

if args.version:
	print("Script version: " + script_version)
	sys.exit(0)

if args.basic:
	args.no_downloads = True
	args.no_copyrights = True
	args.no_files = True

def clean(name):
	remove_chars = [';', ':', '!', "*", "(", ")", "/", ","]
	for i in remove_chars :
		name = name.replace(i, '')
	replace_chars = [' ', '.']
	for i in replace_chars :
		name = name.replace(i, '-')
	return(name)

if args.output == "":
	args.output = clean(args.project_name) + "-" + clean(args.project_version) + ".spdx"

def list_projects(project_string):
	print("Available projects matching '{}':".format(project_string))
	projs = hub.get_projects(parameters={"q":"name:{}".format(project_string)})
	for proj in projs['items']:
		print(" - " + proj['name'])

def get_all_projects():
	projs = hub.get_projects()
	proj_list = []
	for proj in projs['items']:
		proj_list.append(proj['name'])
	return(proj_list)

def list_versions(version_string):
	print("Available versions:")
	vers = hub.get_project_versions(project, parameters={})
	for ver in vers['items']:
		print(" - " + ver['versionName'])

hub = HubInstance()

project = hub.get_project_by_name(args.project_name)
if project == None:
	print("Project '{}' does not exist".format(args.project_name))
	list_projects(args.project_name)
	sys.exit(2)

version = hub.get_version_by_name(project, args.project_version)
if version == None:
	print("Version '{}' does not exist".format(args.project_version))
	list_versions(args.project_version)
	sys.exit(2)
else:
	print("Working on project '{}' version '{}'\n".format(args.project_name, args.project_version))

def backup_file(filename):
	import os, shutil

	if os.path.isfile(filename):
		# Determine root filename so the extension doesn't get longer
		n, e = os.path.splitext(filename)

		# Is e an integer?
		try:
			num = int(e)
			root = n
		except ValueError:
			root = filename

		# Find next available file version
		for i in range(1000):
			new_file = "{}.{:03d}".format(root, i)
			if not os.path.isfile(new_file):
				os.rename(filename, new_file)
				print("INFO: Moved old output file '{}' to '{}'\n".format(filename, new_file))
				return(new_file)
	return("")

if args.output and os.path.exists(args.output):
	backup_file(args.output)

if args.recursive:
	proj_list = get_all_projects()

bom_components = hub.get_version_components(version)

try:
	spdx = [ "SPDXVersion: SPDX-2.2",
		"DataLicense: CC0-1.0",
		"DocumentNamespace: " + version['_meta']['href'],
		"DocumentName: " + project['name'] + "/" + version['versionName']]

	if 'description' in project.keys():
		spdx.append("DocumentComment: <text>" + project['description'] + "</text>")

	spdx += ["SPDXID: SPDXRef-DOCUMENT",
		"## Creation Information",
		"Creator: Tool: Black Duck SPDX export script https://gihub.com/matthewb66/bd_export_spdx",
		"Creator: Person: " + version['createdBy'] ,
		"Created: " + version['createdAt'].split('.')[0] + 'Z',
		"LicenseListVersion: 3.9",
		"## Relationships"]

except Exception as e:
	print('ERROR: Unable to create spdx header\n' + str(e))
	sys.exit(2)

packages = []
spdx_custom_lics_text = []
spdx_custom_lics = []

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
			sp = str(link[0].split(" ")[0]).replace('\n','')
			#
			# Check format
			protocol = sp.split('://')[0]
			if protocol in ['https', 'http', 'git']:
				return(sp)

	except Exception as e:
		#print('ERROR: Cannot get openhub data\n' + str(e))
		return("NOASSERTION")

	return("NOASSERTION")

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
					custom_headers = {'Accept':'text/plain'}
					resp = hub.execute_get(lic_url, custom_headers=custom_headers)
					lic_text = resp.content.decode("utf-8")
					if thislic not in spdx_custom_lics:
						spdx_custom_lics_text += [ 'LicenseID: ' + thislic, 'ExtractedText: <text>' + lic_text + '</text>']
						spdx_custom_lics.append(thislic)
				except:
					pass
			if lic_string == "NOASSERTION":
				lic_string = thislic
			else:
				lic_string = lic_string + " AND " + thislic
				quotes = True

		if quotes:
			lic_string = "(" + lic_string + ")"

	return(lic_string)

def get_orig_data(comp):
	# Get copyrights, CPE
	copyrights = "NOASSERTION"
	cpe = "NOASSERTION"
	try:
		if 'origins' in comp.keys() and len(comp['origins']) > 0:
			orig = comp['origins'][0]
			if 'externalNamespace' in orig.keys() and 'externalId' in orig.keys():
				compver = comp['componentVersionName']
				id = orig['externalId'].split(':')
				if len(id) == 2:
					# Special case for github
					cpe = "cpe:2.3:a:{}:{}:*:*:*:*:*:*".format(orig['externalNamespace'], orig['externalId'])
				elif len(id) == 3:
					cpe = "cpe:2.3:a:{}:*:*:*:*:*:*".format(orig['externalId'])
			link = next((item for item in orig['_meta']['links'] if item["rel"] == "component-origin-copyrights"), None)
			href = link['href'] + "?limit=100"
			custom_headers = {'Accept':'application/vnd.blackducksoftware.copyright-4+json'}
			resp = hub.execute_get(href, custom_headers=custom_headers)
			for copyright in resp.json()['items']:
				if copyright['active']:
					thiscr = copyright['updatedCopyright'].splitlines()[0].strip()
					if thiscr not in copyrights:
						if copyrights == "NOASSERTION":
							copyrights = thiscr
						else:
							copyrights += "\n" + thiscr
		else:
			print("	INFO: No copyright data available due to no assigned origin")
	except:
		pass
	return(copyrights, cpe)

def get_comments(comp):
	# Get comments/annotations
	annotations = ""
	try:
		hrefs = comp['_meta']['links']

		link = next((item for item in hrefs if item["rel"] == "comments"), None)
		if link:
			href = link['href']
			custom_headers = {'Accept':'application/vnd.blackducksoftware.bill-of-materials-6+json'}
			resp = hub.execute_get(href, custom_headers=custom_headers)
			mytime = datetime.datetime.now()
			mytime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
			for comment in resp.json()['items']:
				annotations += "AnnotationDate: " + mytime.strftime("%Y-%m-%dT%H:%M:%S.%fZ") + "\n" + \
				"AnnotationType: OTHER\n" + \
				"Annotator: Person: " + comment['user']['email'] + "\n" + \
				"AnnotationComment :" + comment['comment']  + "\n" + \
				"SPDXREF: " + spdxpackage_name + "\n"
	except:
		pass
	return(annotations)

def get_files(comp):
	# Get files
	try:
		hrefs = comp['_meta']['links']

		retfile = "NOASSERTION"
		link = next((item for item in hrefs if item["rel"] == "matched-files"), None)
		if link:
			href = link['href']
			custom_headers = {'Accept':'application/vnd.blackducksoftware.bill-of-materials-6+json'}
			resp = hub.execute_get(href, custom_headers=custom_headers)
			cfile = resp.json()['items']
			if len(cfile) > 0:
				retfile = cfile[0]['filePath']['path']
	except:
		pass
	return(retfile)

def process_components(bom_components):
	global packages, spdx

	for bom_component in bom_components['items']:

		#DEBUG
# 		if 'jackson-datatype-joda' not in bom_component['componentName']:
# 			continue

		print(" - " + bom_component['componentName'] + "/" + bom_component['componentVersionName'])

		if 'componentVersionName' not in bom_component.keys():
			print("INFO: Skipping component {} which has no assigned version".format(bom_component['componentName']))
			continue

		spdxpackage_name = clean("SPDXRef-Package-" + bom_component['componentName'] + "-" + bom_component['componentVersionName'])

		# First check if this component is a sub-project
		if args.recursive:
			if bom_component['matchTypes'][0] == "MANUAL_BOM_COMPONENT" and bom_component['componentName'] in proj_list:
				sub_project = hub.get_project_by_name(bom_component['componentName'])
				if sub_project != "" and sub_project != None:
					sub_version = hub.get_version_by_name(sub_project, bom_component['componentVersionName'])
					if sub_version != "" and sub_version != None:
						print("Processing project within project '{}'".format(bom_component['componentName']))
						sub_bom_components = hub.get_version_components(sub_version)
						process_components(sub_bom_components)
						continue

		# Get component info
		comp = bom_component['component']
		custom_headers = {'Accept':'application/vnd.blackducksoftware.component-detail-5+json'}
		resp = hub.execute_get(comp, custom_headers=custom_headers)
		kb_component = resp.json()
		openhub_url = next((item for item in kb_component['_meta']['links'] if item["rel"] == "openhub"), None)
		download_url = "NOASSERTION"
		if openhub_url != None and not args.no_downloads:
			download_url = openhub_get_download(openhub_url['href'])

		annotations = get_comments(bom_component)

		lic_string = get_licenses(bom_component)

		copyrights = "NOASSERTION"
		cpe = "NOASSERTION"
		if not args.no_copyrights:
			copyrights, cpe = get_orig_data(bom_component)
			copyrights = '<text>' + copyrights + '</text>'

		package_file = "NOASSERTION"
		if not args.no_files:
			package_file = get_files(bom_component)

		try:
			this_package = [
				"## Black Duck project component",
				"PackageName: " + bom_component['componentName'],
				"SPDXID: " + spdxpackage_name,
				"PackageVersion: " + bom_component['componentVersionName'],
				"PackageFileName: " + package_file,
				"PackageDownloadLocation: " + download_url,
				# PackageChecksum: SHA1: 85ed0817af83a24ad8da68c2b5094de69833983c
				"PackageLicenseConcluded: " + lic_string,
				"PackageLicenseDeclared: " + lic_string,
				# PackageLicenseComments: <text>Other versions available for a commercial license</text>
				# FilesAnalyzed: false
				"ExternalRef: SECURITY cpe23Type {}".format(cpe),
				# ExternalRef: PERSISTENT-ID swh swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2
				# ExternalRef: OTHER LocationRef-acmeforge acmecorp/acmenator/4.1.3-alpha
				# ExternalRefComment: This is the external ref for Acme
			]
			if 'url' in kb_component.keys():
				this_package.append("PackageHomePage: " + kb_component['url'])

		except Exception as e:
			print("SKIPPING component {}".format(bom_component['componentName']) + str(e))
			continue

		if len(bom_component['usages']) > 0 and bom_component['usages'][0] in usage_dict.keys():
			spdx.append("Relationship: SPDXRef-DOCUMENT " + usage_dict[bom_component['usages'][0]] + " " + spdxpackage_name)
		else:
			spdx.append("Relationship: SPDXRef-DOCUMENT CONTAINS " + spdxpackage_name)

		if 'description' in kb_component.keys():
			desc = re.sub('[^a-zA-Z.()\d\s\-:]', '', kb_component['description'])
			this_package.append("PackageDescription: <text>" + desc + "</text>")
		this_package += [ "PackageCopyrightText: " + copyrights, annotations ]

		packages.extend(this_package)

print("Processing components:")
process_components(bom_components)

spdx += ['']
spdx += packages
spdx += ['## Custom Licenses' ]
spdx += spdx_custom_lics_text

print("\nWriting SPDX output file {} ... ".format(args.output), end = '')

try:
	f = open(args.output, "a")

	for line in spdx:
		f.write(line + "\n")
	f.close()

except Exception as e:
	print('ERROR: Unable to create output report file \n' + str(e))
	sys.exit(3)

print("Done")
