#!/usr/bin/env python
import re
import json
import sys

from export_spdx import globals
from export_spdx import config

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


def clean_for_spdx(name):
    newname = re.sub('[;:!*()/,]', '', name)
    newname = re.sub('[ .]', '', newname)
    newname = re.sub('@', '-at-', newname)
    newname = re.sub('_', 'uu', newname)

    return newname


def quote(name):
    remove_chars = ['"', "'"]
    for i in remove_chars:
        name = name.replace(i, '')
    return name


def add_relationship(parent, child, reln):
    mydict = {
        "spdxElementId": quote(parent),
        "relationshipType": quote(reln),
        "relatedSpdxElement": quote(child)
    }
    globals.spdx['relationships'].append(mydict)


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


def write_spdx_file(spdx):
    print("Writing SPDX output file {} ... ".format(config.args.output), end='')

    try:
        with open(config.args.output, 'w') as outfile:
            json.dump(spdx, outfile, indent=4, sort_keys=True)

    except Exception as e:
        print('ERROR: Unable to create output report file \n' + str(e))
        sys.exit(3)

    print("Done")
