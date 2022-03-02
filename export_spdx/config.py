#!/usr/bin/env python
import argparse
import sys
import os

from export_spdx import spdx
from export_spdx import globals

parser = argparse.ArgumentParser(description='"Export SPDX JSON format file for the given project and version"',
                                 prog='bd_export_spdx22_json.py')
parser.add_argument("project_name", type=str, help='Black Duck project name')
parser.add_argument("project_version", type=str, help='Black Duck version name')
parser.add_argument("-v", "--version", help="Print script version and exit", action='store_true')
parser.add_argument("-o", "--output", type=str,
                    help="Output SPDX file name (SPDX JSON format) - default '<proj>-<ver>.json'", default="")
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
parser.add_argument("-x", "--exclude_ignored_components",
                    help="Exclude components marked ignored in the BOM", action='store_true')
parser.add_argument("--blackduck_url", type=str,
                    help="Black Duck server URL (can also be set as env. var. BLACKDUCK_URL)", default="")
parser.add_argument("--blackduck_api_token", type=str,
                    help="Black Duck API token URL (can also be set as env. var. BLACKDUCK_API_TOKEN)", default="")
parser.add_argument("--blackduck_trust_certs", help="BLACKDUCK trust certs", action='store_true')
parser.add_argument("--blackduck_timeout", help="BD Server requests timeout (seconds - default 15)", default=15)
parser.add_argument("--debug", help="Turn on debug messages", action='store_true')

args = parser.parse_args()


def check_params():
    if args.version:
        print("Script version: " + globals.script_version)
        sys.exit(0)

    if args.basic:
        args.download_loc = False
        args.no_copyrights = True
        args.no_files = True
    if args.output == "":
        args.output = spdx.clean_for_spdx(args.project_name + "-" + args.project_version) + ".json"

    if args.output and os.path.exists(args.output):
        backup_file(args.output)


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
