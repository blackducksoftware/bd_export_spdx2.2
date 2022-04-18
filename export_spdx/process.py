#!/usr/bin/env python
import datetime
import re
import aiohttp
import asyncio
import time
import platform

from export_spdx import globals
from export_spdx import spdx
from export_spdx import config
from export_spdx import projects
from export_spdx import data


def process_comp(comps_dict, tcomp, comp_data_dict):
    cver = tcomp['componentVersion']
    if cver in comps_dict.keys():
        # ind = compverlist.index(tcomp['componentVersion'])
        bomentry = comps_dict[cver]
    else:
        bomentry = tcomp

    spdxpackage_name = spdx.clean_for_spdx(
        "SPDXRef-Package-" + tcomp['componentName'] + "-" + tcomp['componentVersionName'])

    if spdxpackage_name in globals.spdx_ids:
        return spdxpackage_name

    globals.spdx_ids[spdxpackage_name] = 1

    # openhub_url = None

    if cver not in globals.processed_comp_list:
        download_url = "NOASSERTION"

        # fcomp = globals.bd.get_json(tcomp['component'])  # CHECK THIS
        #
        openhub_url = next((item for item in bomentry['_meta']['links'] if item["rel"] == "openhub"), None)
        if config.args.download_loc and openhub_url is not None:
            download_url = data.openhub_get_download(openhub_url['href'])

        copyrights = "NOASSERTION"
        # cpe = "NOASSERTION"
        pkg = "NOASSERTION"
        if not config.args.no_copyrights:
            # copyrights, cpe, pkg = get_orig_data(bomentry)
            copyrights = comp_data_dict[cver]['copyrights']

            if 'origins' in bomentry.keys() and len(bomentry['origins']) > 0:
                orig = bomentry['origins'][0]
                if 'externalNamespace' in orig.keys() and 'externalId' in orig.keys():
                    pkg = data.calculate_purl(orig['externalNamespace'], orig['externalId'])

        package_file = "NOASSERTION"
        if not config.args.no_files:
            package_file = comp_data_dict[cver]['files']

        desc = 'NOASSERTION'
        if 'description' in tcomp.keys():
            desc = re.sub("[^a-zA-Z.()\d\s\-:]", '', bomentry['description'])

        annotations = comp_data_dict[cver]['comments']
        lic_string = comp_data_dict[cver]['licenses']

        component_package_supplier = ''

        # homepage = 'NOASSERTION'
        homepage = comp_data_dict[cver]['url']

        bom_package_supplier = comp_data_dict[cver]['supplier']

        packageinfo = "This is a"

        if bomentry['componentType'] == 'CUSTOM_COMPONENT':
            packageinfo = packageinfo + " custom component"
        if bomentry['componentType'] == 'SUB_PROJECT':
            packageinfo = packageinfo + " sub project"
        else:
            packageinfo = packageinfo + "n open source component from the Black Duck Knowledge Base"

        if len(bomentry['matchTypes']) > 0:
            firstType = bomentry['matchTypes'][0]
            if firstType == 'MANUAL_BOM_COMPONENT':
                packageinfo = packageinfo + " which was manually added"
            else:
                packageinfo = packageinfo + " which was automatically detected"
                if firstType == 'FILE_EXACT':
                    packageinfo = packageinfo + " as a direct file match"
                elif firstType == 'SNIPPET':
                    packageinfo = packageinfo + " as a code snippet"
                elif firstType == 'FILE_DEPENDENCY_DIRECT':
                    packageinfo = packageinfo + " as a directly declared dependency"
                elif firstType == 'FILE_DEPENDENCY_TRANSITIVE':
                    packageinfo = packageinfo + " as a transitive dependency"

        packagesuppliername = ''

        if bom_package_supplier is not None and len(bom_package_supplier) > 0:
            packageinfo = packageinfo + ", the PackageSupplier was provided by the user at the BOM level"
            packagesuppliername = packagesuppliername + bom_package_supplier
            pkg = "supplier:{}/{}/{}".format(bom_package_supplier.replace("Organization: ", ""), tcomp['componentName'],
                                             tcomp['componentVersionName'])
        elif component_package_supplier is not None and len(component_package_supplier) > 0:
            packageinfo = packageinfo + ", the PackageSupplier was populated in the component"
            packagesuppliername = packagesuppliername + component_package_supplier
            pkg = "supplier:{}/{}/{}".format(component_package_supplier.replace("Organization: ", ""),
                                             tcomp['componentName'], tcomp['componentVersionName'])
        elif bomentry['origins'] is not None and len(bomentry['origins']) > 0:
            packagesuppliername = packagesuppliername + "Organization: " + bomentry['origins'][0]['externalNamespace']
            packageinfo = packageinfo + ", the PackageSupplier was based on the externalNamespace"
        else:
            packageinfo = packageinfo + ", the PackageSupplier was not populated"
            packagesuppliername = packagesuppliername + "NOASSERTION"

        # TO DO - use packagesuppliername somewhere

        thisdict = {
            "SPDXID": spdx.quote(spdxpackage_name),
            "name": spdx.quote(tcomp['componentName']),
            "versionInfo": spdx.quote(tcomp['componentVersionName']),
            "packageFileName": spdx.quote(package_file),
            "description": spdx.quote(desc),
            "downloadLocation": spdx.quote(download_url),
            "packageHomepage": spdx.quote(homepage),
            # PackageChecksum: SHA1: 85ed0817af83a24ad8da68c2b5094de69833983c,
            "licenseConcluded": spdx.quote(lic_string),
            "licenseDeclared": spdx.quote(lic_string),
            "licenseComments": "The concluded license was taken from the package level",
            "packageSupplier": packagesuppliername,
            # PackageLicenseComments: <text>Other versions available for a commercial license</text>,
            "filesAnalyzed": False,
            "packageComment": spdx.quote(packageinfo),
            # "ExternalRef: SECURITY cpe23Type {}".format(cpe),
            # "ExternalRef: PACKAGE-MANAGER purl pkg:" + pkg,
            # ExternalRef: PERSISTENT-ID swh swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2,
            # ExternalRef: OTHER LocationRef-acmeforge acmecorp/acmenator/4.1.3-alpha,
            # ExternalRefComment: This is the external ref for Acme,
            "copyrightText": spdx.quote(copyrights),
            "annotations": annotations,
        }

        if pkg != '':
            thisdict["externalRefs"] = [
                {
                    "referenceLocator": pkg,
                    "referenceCategory": "PACKAGE_MANAGER",
                    "referenceType": "purl"
                },
                {
                    "referenceCategory": "OTHER",
                    "referenceType": "BlackDuckHub-Component",
                    "referenceLocator": tcomp['component'],
                },
                {
                    "referenceCategory": "OTHER",
                    "referenceType": "BlackDuckHub-Component-Version",
                    "referenceLocator": cver
                }
            ]
            if openhub_url is not None:
                thisdict['externalRefs'].append({
                    "referenceCategory": "OTHER",
                    "referenceType": "OpenHub",
                    "referenceLocator": openhub_url
                })

        globals.spdx['packages'].append(thisdict)
    return spdxpackage_name


def process_children(pkgname, compverurl, child_url, indenttext, comps_dict, comp_data_dict):
    # res = globals.bd.get_json(child_url + '?limit=5000')
    items = data.get_data_paged(globals.bd, child_url, {})

    count = 0
    for child in items:
        if 'componentName' in child and 'componentVersionName' in child:
            if config.args.debug:
                print("{}{}/{}".format(indenttext, child['componentName'], child['componentVersionName']))
        else:
            # No version - skip
            print("{}{}/{} (SKIPPED)".format(indenttext, child['componentName'], '?'))
            continue

        childpkgname = process_comp(comps_dict, child, comp_data_dict)
        count += 1
        if childpkgname != '':
            reln = False
            for tchecktype in globals.matchtype_depends_dict.keys():
                if tchecktype in child['matchTypes']:
                    spdx.add_relationship(pkgname, childpkgname, globals.matchtype_depends_dict[tchecktype])
                    reln = True
                    break
            if not reln:
                for tchecktype in globals.matchtype_contains_dict.keys():
                    if tchecktype in child['matchTypes']:
                        spdx.add_relationship(pkgname, childpkgname,
                                              globals.matchtype_contains_dict[tchecktype])
                        break
            globals.processed_comp_list.append(child['componentVersion'])
        else:
            pass

        if len(child['_meta']['links']) > 2:
            thisref = [d['href'] for d in child['_meta']['links'] if d['rel'] == 'children']
            if len(thisref) > 0:
                count += process_children(childpkgname, child['componentVersion'], thisref[0], "    " + indenttext,
                                          comps_dict, comp_data_dict)

    return count


def process_comp_relationship(parentname, childname, mtypes):
    reln = False
    for tchecktype in globals.matchtype_depends_dict.keys():
        if tchecktype in mtypes:
            spdx.add_relationship(parentname, childname, globals.matchtype_depends_dict[tchecktype])
            reln = True
            break
    if not reln:
        for tchecktype in globals.matchtype_contains_dict.keys():
            if tchecktype in mtypes:
                spdx.add_relationship(parentname, childname, globals.matchtype_contains_dict[tchecktype])
                break


def process_project(project, version, projspdxname, hcomps, bearer_token, exclude_ignored=False):
    # project, version = check_projver(proj, ver)

    start_time = time.time()
    print('Getting component list ... ', end='')
    bom_compsdict = data.get_bom_components(version, exclude_ignored)
    print("({})".format(str(len(bom_compsdict))))
    if config.args.debug:
        print("--- %s seconds ---" % (time.time() - start_time))

    start_time = time.time()
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    comp_data_dict = asyncio.run(async_main(bom_compsdict, bearer_token, version))
    if config.args.debug:
        print("--- %s seconds ---" % (time.time() - start_time))

    #
    # Process hierarchical BOM elements
    start_time = time.time()
    print('Processing hierarchical BOM ...')
    compcount = 0
    for hcomp in hcomps:
        if 'componentVersionName' in hcomp:
            compname = "{}/{}".format(hcomp['componentName'], hcomp['componentVersionName'])
            if config.args.debug:
                print(compname)
        else:
            print("{}/? - (no version - skipping)".format(hcomp['componentName']))
            continue

        pkgname = process_comp(bom_compsdict, hcomp, comp_data_dict)

        if pkgname != '':
            process_comp_relationship(projspdxname, pkgname, hcomp['matchTypes'])
            globals.processed_comp_list.append(hcomp['componentVersion'])
            compcount += 1

            href = [d['href'] for d in hcomp['_meta']['links'] if d['rel'] == 'children']
            if len(href) > 0:
                compcount += process_children(pkgname, hcomp['componentVersion'], href[0], "--> ", bom_compsdict,
                                              comp_data_dict)

    print('Processed {} hierarchical components'.format(compcount))
    if config.args.debug:
        print("--- %s seconds ---" % (time.time() - start_time))

    #
    # Process all entries to find entries not in hierarchical BOM and sub-projects
    print('Processing other components ...')
    start_time = time.time()
    compcount = 0
    for key, bom_component in bom_compsdict.items():
        if 'componentVersion' not in bom_component.keys():
            print(
                "INFO: Skipping component {} which has no assigned version".format(bom_component['componentName']))
            continue

        compname = bom_component['componentName'] + "/" + bom_component['componentVersionName']
        if bom_component['componentVersion'] in globals.processed_comp_list:
            continue
        # Check if this component is a sub-project
        # if bom_component['matchTypes'][0] == "MANUAL_BOM_COMPONENT":
        if config.args.debug:
            print(compname)
        compcount += 1

        pkgname = process_comp(bom_compsdict, bom_component, comp_data_dict)

        process_comp_relationship(projspdxname, pkgname, bom_component['matchTypes'])

        if config.args.recursive and bom_component['componentName'] in globals.proj_list:
            #
            # Need to check if this component is a sub-project
            params = {
                'q': "name:" + bom_component['componentName'],
            }
            sub_projects = globals.bd.get_resource('projects', params=params)
            for sub_proj in sub_projects:
                params = {
                    'q': "versionName:" + bom_component['componentVersionName'],
                }
                sub_versions = globals.bd.get_resource('versions', parent=sub_proj, params=params)
                for sub_ver in sub_versions:
                    print("Processing project within project '{}'".format(
                        bom_component['componentName'] + '/' + bom_component['componentVersionName']))

                    res = globals.bd.list_resources(parent=sub_ver)
                    # if 'components' in res:
                    #     sub_comps = globals.bd.get_resource('components', parent=sub_ver)
                    # else:
                    #     thishref = res['href'] + "/components?limit=2000"
                    #     headers = {
                    #         'accept': "application/vnd.blackducksoftware.bill-of-materials-6+json",
                    #     }
                    #     res2 = globals.bd.get_json(thishref, headers=headers)
                    #     sub_comps = res2['items']

                    if 'hierarchical-components' in res:
                        sub_hierarchical_bom = globals.bd.get_resource('hierarchical-components', parent=sub_ver)
                    else:
                        thishref = res['href'] + "/hierarchical-components?limit=2000"
                        headers = {
                            'accept': "application/vnd.blackducksoftware.bill-of-materials-6+json",
                        }
                        res2 = globals.bd.get_json(thishref, headers=headers)
                        sub_hierarchical_bom = res2['items']

                    subprojspdxname = spdx.clean_for_spdx(bom_component['componentName'] + '/' +
                                                          bom_component['componentVersionName'])
                    # subproj_compsdict = get_bom_components(sub_ver)
                    # subproj_comp_data_dict = asyncio.run(async_main(subproj_compsdict, bearer_token, res['href']))
                    subproj, subver = projects.check_projver(bom_component['componentName'],
                                                             bom_component['componentVersionName'])
                    compcount += process_project(subproj, subver,
                                                 subprojspdxname, sub_hierarchical_bom, bearer_token)
                    break
                break

    print('Processed {} other components'.format(compcount))
    if config.args.debug:
        print("--- %s seconds ---" % (time.time() - start_time))
    # print('Output {} Overall components'.format(len(globals.processed_comp_list)))

    return compcount


async def async_main(compsdict, token, ver):
    async with aiohttp.ClientSession() as session:
        copyright_tasks = []
        comment_tasks = []
        file_tasks = []
        lic_tasks = []
        url_tasks = []
        supplier_tasks = []
        # child_tasks = []
        for url, comp in compsdict.items():
            if config.args.debug:
                print(comp['componentName'] + '/' + comp['componentVersionName'])
            copyright_task = asyncio.ensure_future(async_get_copyrights(session, comp, token))
            copyright_tasks.append(copyright_task)

            comment_task = asyncio.ensure_future(async_get_comments(session, comp, token))
            comment_tasks.append(comment_task)

            file_task = asyncio.ensure_future(async_get_files(session, comp, token))
            file_tasks.append(file_task)

            lic_task = asyncio.ensure_future(async_get_licenses(session, comp, token))
            lic_tasks.append(lic_task)

            url_task = asyncio.ensure_future(async_get_url(session, comp, token))
            url_tasks.append(url_task)

            supplier_task = asyncio.ensure_future(async_get_supplier(session, comp, token))
            supplier_tasks.append(supplier_task)

        print('Getting component data ... ')
        all_copyrights = dict(await asyncio.gather(*copyright_tasks))
        all_comments = dict(await asyncio.gather(*comment_tasks))
        all_files = dict(await asyncio.gather(*file_tasks))
        all_lics = dict(await asyncio.gather(*lic_tasks))
        all_urls = dict(await asyncio.gather(*url_tasks))
        all_suppliers = dict(await asyncio.gather(*supplier_tasks))

        # all_children = dict(await asyncio.gather(*child_tasks))
        await asyncio.sleep(0.250)

    comp_data_dict = {}
    for cvurl in compsdict.keys():
        comp_data_dict[cvurl] = {
            'copyrights': all_copyrights[cvurl],
            'comments': all_comments[cvurl],
            'files': all_files[cvurl],
            'licenses': all_lics[cvurl],
            'url': all_urls[cvurl],
            'supplier': all_suppliers[cvurl]
        }
    return comp_data_dict


async def async_get_copyrights(session, comp, token):
    if not globals.verify:
        ssl = False
    else:
        ssl = None

    copyrights = "NOASSERTION"
    if len(comp['origins']) < 1:
        return comp['componentVersion'], copyrights

    orig = comp['origins'][0]
    link = next((item for item in orig['_meta']['links'] if item["rel"] == "component-origin-copyrights"), None)
    thishref = link['href'] + "?limit=100"
    headers = {
        'accept': "application/vnd.blackducksoftware.copyright-4+json",
        'Authorization': f'Bearer {token}',
    }
    # resp = globals.bd.get_json(thishref, headers=headers)
    async with session.get(thishref, headers=headers, ssl=ssl) as resp:
        result_data = await resp.json()
        for copyrt in result_data['items']:
            if copyrt['active']:
                thiscr = copyrt['updatedCopyright'].splitlines()[0].strip()
                if thiscr not in copyrights:
                    if copyrights == "NOASSERTION":
                        copyrights = thiscr
                    else:
                        copyrights += "\n" + thiscr
    return comp['componentVersion'], copyrights


async def async_get_comments(session, comp, token):
    if not globals.verify:
        ssl = False
    else:
        ssl = None

    annotations = []
    hrefs = comp['_meta']['links']

    link = next((item for item in hrefs if item["rel"] == "comments"), None)
    if link:
        thishref = link['href']
        headers = {
            'Authorization': f'Bearer {token}',
            'accept': "application/vnd.blackducksoftware.bill-of-materials-6+json",
        }
        # resp = globals.bd.get_json(thishref, headers=headers)
        async with session.get(thishref, headers=headers, ssl=ssl) as resp:
            result_data = await resp.json()
            mytime = datetime.datetime.now()
            # mytime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            for comment in result_data['items']:
                annotations.append(
                    {
                        "annotationDate": spdx.quote(mytime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
                        "annotationType": "OTHER",
                        "annotator": spdx.quote("Person: " + comment['user']['email']),
                        "comment": spdx.quote(comment['comment']),
                    }
                )
    return comp['componentVersion'], annotations


async def async_get_files(session, comp, token):
    if not globals.verify:
        ssl = False
    else:
        ssl = None

    retfile = "NOASSERTION"
    hrefs = comp['_meta']['links']

    link = next((item for item in hrefs if item["rel"] == "matched-files"), None)
    if link:
        thishref = link['href']
        headers = {
            'Authorization': f'Bearer {token}',
            'accept': "application/vnd.blackducksoftware.bill-of-materials-6+json",
        }

        async with session.get(thishref, headers=headers, ssl=ssl) as resp:
            result_data = await resp.json()
            cfile = result_data['items']
            if len(cfile) > 0:
                rfile = cfile[0]['filePath']['path']
                for ext in ['.jar', '.ear', '.war', '.zip', '.gz', '.tar', '.xz', '.lz', '.bz2', '.7z',
                            '.rar', '.rar', '.cpio', '.Z', '.lz4', '.lha', '.arj', '.rpm', '.deb', '.dmg',
                            '.gz', '.whl']:
                    if rfile.endswith(ext):
                        retfile = rfile
    return comp['componentVersion'], retfile


async def async_get_licenses(session, lcomp, token):
    if not globals.verify:
        ssl = False
    else:
        ssl = None

    # Get licenses
    lic_string = "NOASSERTION"
    quotes = False
    license_type = "NONE"
    if 'licenses' in lcomp.keys():
        proc_item = lcomp['licenses']

        if len(proc_item[0]['licenses']) > 1:
            license_type = proc_item[0]['licenseType']
            proc_item = proc_item[0]['licenses']

        for lic in proc_item:
            thislic = ''
            if 'spdxId' in lic:
                thislic = lic['spdxId']
                if thislic in spdx.spdx_deprecated_dict.keys():
                    thislic = spdx.spdx_deprecated_dict[thislic]
            else:
                # Custom license
                try:
                    thislic = 'LicenseRef-' + spdx.clean_for_spdx(lic['licenseDisplay'] + '-' + lcomp['componentName'])
                    lic_ref = lic['license'].split("/")[-1]
                    headers = {
                        'accept': "text/plain",
                        'Authorization': f'Bearer {token}',
                    }
                    # resp = globals.bd.session.get('/api/licenses/' + lic_ref + '/text', headers=headers)
                    thishref = f"{globals.bd.base_url}/api/licenses/{lic_ref}/text"
                    async with session.get(thishref, headers=headers, ssl=ssl) as resp:
                        # lic_text = await resp.content.decode("utf-8")
                        lic_text = await resp.text('utf-8')
                        if thislic not in globals.spdx_lics:
                            mydict = {
                                'licenseID': spdx.quote(thislic),
                                'extractedText': spdx.quote(lic_text)
                            }
                            globals.spdx["hasExtractedLicensingInfos"].append(mydict)
                            globals.spdx_lics.append(thislic)
                except Exception as exc:
                    pass
            if lic_string == "NOASSERTION":
                lic_string = thislic
            else:
                if license_type == "DISJUNCTIVE":
                    lic_string = lic_string + " OR " + thislic
                else:
                    lic_string = lic_string + " AND " + thislic
                quotes = True

        if quotes:
            lic_string = "(" + lic_string + ")"

    return lcomp['componentVersion'], lic_string


async def async_get_url(session, comp, token):
    if not globals.verify:
        ssl = False
    else:
        ssl = None

    url = "NOASSERTION"
    if 'component' not in comp.keys():
        return comp['componentVersion'], url

    link = comp['component']
    headers = {
        'accept': "application/vnd.blackducksoftware.bill-of-materials-6+json",
        'Authorization': f'Bearer {token}',
    }
    # resp = globals.bd.get_json(thishref, headers=headers)
    async with session.get(link, headers=headers, ssl=ssl) as resp:
        result_data = await resp.json()
        if 'url' in result_data.keys():
            url = result_data['url']
    return comp['componentVersion'], url


async def async_get_supplier(session, comp, token):
    if not globals.verify:
        ssl = False
    else:
        ssl = None

    supplier_name = ''
    hrefs = comp['_meta']['links']

    link = next((item for item in hrefs if item["rel"] == "custom-fields"), None)
    if link:
        thishref = link['href']
        headers = {
            'Authorization': f'Bearer {token}',
            'accept': "application/vnd.blackducksoftware.bill-of-materials-6+json",
        }

        async with session.get(thishref, headers=headers, ssl=ssl) as resp:
            result_data = await resp.json()
            cfields = result_data['items']
            sbom_field = next((item for item in cfields if item['label'] == globals.SBOM_CUSTOM_SUPPLIER_NAME),
                              None)

            if sbom_field is not None and len(sbom_field['values']) > 0:
                supplier_name = sbom_field['values'][0]

    return comp['componentVersion'], supplier_name
