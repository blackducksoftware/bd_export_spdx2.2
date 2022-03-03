#!/usr/bin/env python
script_version = "0.23"

processed_comp_list = []
spdx_lics = []

# The name of a custom attribute which should override the default package supplier
SBOM_CUSTOM_SUPPLIER_NAME = "PackageSupplier"

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

spdx = dict()
spdx['packages'] = []
spdx['relationships'] = []
spdx['snippets'] = []
spdx['hasExtractedLicensingInfos'] = []

spdx_ids = {}
proj_list = []

verify = True

bd = None
