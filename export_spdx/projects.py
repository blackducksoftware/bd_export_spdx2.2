#!/usr/bin/env python
import sys

from export_spdx import globals, data


def get_all_projects():
    projs = globals.bd.get_resource('projects', items=True)

    projlist = []
    for proj in projs:
        projlist.append(proj['name'])
    return projlist


def check_projver(proj, ver):
    params = {
        'q': "name:" + proj,
        'sort': 'name',
    }

    projects = globals.bd.get_resource('projects', params=params)
    for p in projects:
        if p['name'] == proj:
            versions = globals.bd.get_resource('versions', parent=p, params=params)
            for v in versions:
                if v['versionName'] == ver:
                    return p, v
            break
    else:
        print("Version '{}' does not exist in project '{}'".format(ver, proj))
        sys.exit(2)

    print("Project '{}' does not exist".format(proj))
    print('Available projects:')
    projects = globals.bd.get_resource('projects')
    for proj in projects:
        print(proj['name'])
    sys.exit(2)


def get_bom_components(verdict):
    comp_dict = {}
    res = globals.bd.list_resources(verdict)
    # if 'components' not in res:
    if True:
        # Getting the component list via a request is much quicker than the new Client model
        # thishref = res['href'] + "/components?limit=5000"
        thishref = res['href'] + "/components"

        headers = {
            'accept': "application/vnd.blackducksoftware.bill-of-materials-6+json",
        }
        # res = globals.bd.get_json(thishref, headers=headers)
        # bom_comps = res['items']
        bom_comps = data.get_data_paged(globals.bd, thishref, headers)
    # else:
    #     bom_comps = globals.bd.get_resource('components', parent=ver)
    for comp in bom_comps:
        if 'componentVersion' not in comp:
            continue
        compver = comp['componentVersion']

        comp_dict[compver] = comp

    return comp_dict
