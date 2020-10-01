# Synopsys Black Duck - bd_export_spdx22.py
# OVERVIEW

This script is provided under an OSS license (specified in the LICENSE file) to allow users to export an SPDX version 2.2 tag-value file from Black Duck projects.

It does not represent any extension of licensed functionality of Synopsys software itself and is provided as-is, without warranty or liability.

# DESCRIPTION

The script is designed to export an SPDX version 2.2 tag-value file from a Black Duck project.

It relies on the `hub-rest-api-python` package to access the Black Duck APIs (see prerequisites below to install and configure this package).

The project name and version need to be specified. If the project name is not matched in the server then the list of projects matching the supplied project string will be displayed (and the script will terminate). If the version name is not matched for the specified project, then the list of all versions will be displayed  (and the script will terminate).

The output file in SPDX tag-value format can optionally be specified; the project name and version name with .spdx extension will be used for the default filename if nor specified. If the output file already exists, it will be renamed using a numeric extension (for example `.001`).

The optional `--recursive` option will traverse sub-projects to include all leaf components. If not specified, and sub-projects exist in the specified project, then the sub-projects will be skipped.

# PREREQUISITES

1. Python 3 must be installed.

1. Install the following packages in the virtualenv:

       pip install blackduck lxml

1. An API key for the Black Duck server must be configured within the `.restconfig.json` file in the script invocation folder - see the `CONFIG FILE` section below.

# CONFIG FILE

Configure the Black Duck connection within the `.restconfig.json` file in the script invocation folder - example contents:

    {
      "baseurl": "https://myhub.blackducksoftware.com",
      "api_token": "YWZkOTE5NGYtNzUxYS00NDFmLWJjNzItYmYwY2VlNDIxYzUwOmE4NjNlNmEzLWRlNTItNGFiMC04YTYwLWRBBWQ2MDFXXjA0Mg==",
      "insecure": true,
      "debug": false
    }

# USAGE

The `bd_export_spdx22.py` script can be invoked as follows:

       Usage: export_spdx22.py [-h] [-o OUTPUT] [-r] [--no_downloads] [--no_copyrights]
                      [--no_files] [-b]
                      project_name version

       "Export SPDX for the given project and version"

       Positional arguments:
         project_name          Black Duck project name
         version               Black Duck version name

       Optional arguments:
         -h, --help            show this help message and exit
         -o OUTPUT, --output OUTPUT
                               Output SPDX file name (SPDX tag format) - default
                               '<proj>-<ver>.spdx'
         -r, --recursive       Scan sub-projects within projects (default = false)
         --no_downloads        Do not identify component download link extracted from
                               Openhub (speeds up processing - default=false)
         --no_copyrights       Do not export copyright data for components (speeds up
                               processing - default=false)
         --no_files            Do not export file data for components (speeds up
                               processing - default=false)
         -b, --basic           Do not export copyright, download link or package file
                               data (speeds up processing - same as using '--
                               no_downloads --no_copyrights --no_files')

If `project_name` does not match a single project then all matching projects will be listed and the script will terminate.

If `version` does not match a single project version then all matching versions will be listed and the script will terminate.

The `--output out_file` or `-o out_file` option specifies the output file. If this file already exists, the previous version will be renamed with a unique number (e.g. .001). The default file name `<project>-<version>.spdx` will be used if not specified.

The `--recursive` or `-r` option will cause Black Duck sub-projects to be processed, adding the components of sub-projects to the overall SPDX output file. If the processed project version contains sub-projects and this option is not specified, they will be ignored.

The `--no_downloads` option will stop the processing of component download locations from Openhub.net (PackageDownloadLocation tag), reducing the number of API calls and time to complete the script.

The `--no_copyrights` option will stop the processing of component copyright text (PackageCopyrightText tag) reducing the number of API calls and time to complete the script.

The `--no_files` option will stop the processing of component filename (PackageFileName tag) reducing the number of API calls and time to complete the script.

The `--basic` or `-b` option will stop the processing of copy, download link or package file (same as using `--no_downloads --no_copyrights --no_files` options) reducing the number of API calls and time to complete the script.
