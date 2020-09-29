#!/usr/bin/env python

import argparse
import json
import logging
import sys, time, datetime, os
from lxml import html
import requests
# from zipfile import ZipFile

from blackduck.HubRestApi import HubInstance

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', stream=sys.stderr, level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

lic_dict = {
"BSD Zero Clause License": "0BSD",
"Attribution Assurance License": "AAL",
"Abstyles License": "Abstyles",
"Adobe Systems Incorporated Source Code License Agreement": "Adobe-2006",
"Adobe Glyph List License": "Adobe-Glyph",
"Amazon Digital Services License": "ADSL",
"Academic Free License v1.1": "AFL-1.1",
"Academic Free License v1.2": "AFL-1.2",
"Academic Free License v2.0": "AFL-2.0",
"Academic Free License v2.1": "AFL-2.1",
"Academic Free License v3.0": "AFL-3.0",
"Afmparse License": "Afmparse",
"Affero General Public License v1.0 only": "AGPL-1.0-only",
"Affero General Public License v1.0 or later": "AGPL-1.0-or-later",
"GNU Affero General Public License v3.0 only": "AGPL-3.0-only",
"GNU Affero General Public License v3.0 or later": "AGPL-3.0-or-later",
"Aladdin Free Public License": "Aladdin",
"AMD's plpa_map.c License": "AMDPLPA",
"Apple MIT License": "AML",
"Academy of Motion Picture Arts and Sciences BSD": "AMPAS",
"ANTLR Software Rights Notice": "ANTLR-PD",
"Apache License 1.0": "Apache-1.0",
"Apache License 1.1": "Apache-1.1",
"Apache License 2.0": "Apache-2.0",
"Adobe Postscript AFM License": "APAFML",
"Adaptive Public License 1.0": "APL-1.0",
"Apple Public Source License 1.0": "APSL-1.0",
"Apple Public Source License 1.1": "APSL-1.1",
"Apple Public Source License 1.2": "APSL-1.2",
"Apple Public Source License 2.0": "APSL-2.0",
"Artistic License 1.0": "Artistic-1.0",
"Artistic License 1.0 w/clause 8": "Artistic-1.0-cl8",
"Artistic License 1.0 (Perl)": "Artistic-1.0-Perl",
"Artistic License 2.0": "Artistic-2.0",
"Bahyph License": "Bahyph",
"Barr License": "Barr",
"Beerware License": "Beerware",
"BitTorrent Open Source License v1.0": "BitTorrent-1.0",
"BitTorrent Open Source License v1.1": "BitTorrent-1.1",
"SQLite Blessing": "blessing",
"Blue Oak Model License 1.0.0": "BlueOak-1.0.0",
"Borceux license": "Borceux",
"BSD 1-Clause License": "BSD-1-Clause",
"BSD 2-Clause 'Simplified' License": "BSD-2-Clause",
"BSD-2-Clause Plus Patent License": "BSD-2-Clause-Patent",
"BSD 2-Clause with views sentence": "BSD-2-Clause-Views",
"BSD 3-Clause 'New' or 'Revised' License": "BSD-3-Clause",
"BSD with attribution": "BSD-3-Clause-Attribution",
"BSD 3-Clause Clear License": "BSD-3-Clause-Clear",
"Lawrence Berkeley National Labs BSD variant license": "BSD-3-Clause-LBNL",
"BSD 3-Clause No Nuclear License": "BSD-3-Clause-No-Nuclear-License",
"BSD 3-Clause No Nuclear License 2014": "BSD-3-Clause-No-Nuclear-License-2014",
"BSD 3-Clause No Nuclear Warranty": "BSD-3-Clause-No-Nuclear-Warranty",
"BSD 3-Clause Open MPI variant": "BSD-3-Clause-Open-MPI",
"BSD 4-Clause 'Original' or 'Old' License": "BSD-4-Clause",
"BSD-4-Clause (University of California-Specific)": "BSD-4-Clause-UC",
"BSD Protection License": "BSD-Protection",
"BSD Source Code Attribution": "BSD-Source-Code",
"Boost Software License 1.0": "BSL-1.0",
"bzip2 and libbzip2 License v1.0.5": "bzip2-1.0.5",
"bzip2 and libbzip2 License v1.0.6": "bzip2-1.0.6",
"Cryptographic Autonomy License 1.0": "CAL-1.0",
"Cryptographic Autonomy License 1.0 (Combined Work Exception)": "CAL-1.0-Combined-Work-Exception",
"Caldera License": "Caldera",
"Computer Associates Trusted Open Source License 1.1": "CATOSL-1.1",
"Creative Commons Attribution 1.0 Generic": "CC-BY-1.0",
"Creative Commons Attribution 2.0 Generic": "CC-BY-2.0",
"Creative Commons Attribution 2.5 Generic": "CC-BY-2.5",
"Creative Commons Attribution 3.0 Unported": "CC-BY-3.0",
"Creative Commons Attribution 3.0 Austria": "CC-BY-3.0-AT",
"Creative Commons Attribution 4.0 International": "CC-BY-4.0",
"Creative Commons Attribution Non Commercial 1.0 Generic": "CC-BY-NC-1.0",
"Creative Commons Attribution Non Commercial 2.0 Generic": "CC-BY-NC-2.0",
"Creative Commons Attribution Non Commercial 2.5 Generic": "CC-BY-NC-2.5",
"Creative Commons Attribution Non Commercial 3.0 Unported": "CC-BY-NC-3.0",
"Creative Commons Attribution Non Commercial 4.0 International": "CC-BY-NC-4.0",
"Creative Commons Attribution Non Commercial No Derivatives 1.0 Generic": "CC-BY-NC-ND-1.0",
"Creative Commons Attribution Non Commercial No Derivatives 2.0 Generic": "CC-BY-NC-ND-2.0",
"Creative Commons Attribution Non Commercial No Derivatives 2.5 Generic": "CC-BY-NC-ND-2.5",
"Creative Commons Attribution Non Commercial No Derivatives 3.0 Unported": "CC-BY-NC-ND-3.0",
"Creative Commons Attribution Non Commercial No Derivatives 3.0 IGO": "CC-BY-NC-ND-3.0-IGO",
"Creative Commons Attribution Non Commercial No Derivatives 4.0 International": "CC-BY-NC-ND-4.0",
"Creative Commons Attribution Non Commercial Share Alike 1.0 Generic": "CC-BY-NC-SA-1.0",
"Creative Commons Attribution Non Commercial Share Alike 2.0 Generic": "CC-BY-NC-SA-2.0",
"Creative Commons Attribution Non Commercial Share Alike 2.5 Generic": "CC-BY-NC-SA-2.5",
"Creative Commons Attribution Non Commercial Share Alike 3.0 Unported": "CC-BY-NC-SA-3.0",
"Creative Commons Attribution Non Commercial Share Alike 4.0 International": "CC-BY-NC-SA-4.0",
"Creative Commons Attribution No Derivatives 1.0 Generic": "CC-BY-ND-1.0",
"Creative Commons Attribution No Derivatives 2.0 Generic": "CC-BY-ND-2.0",
"Creative Commons Attribution No Derivatives 2.5 Generic": "CC-BY-ND-2.5",
"Creative Commons Attribution No Derivatives 3.0 Unported": "CC-BY-ND-3.0",
"Creative Commons Attribution No Derivatives 4.0 International": "CC-BY-ND-4.0",
"Creative Commons Attribution Share Alike 1.0 Generic": "CC-BY-SA-1.0",
"Creative Commons Attribution Share Alike 2.0 Generic": "CC-BY-SA-2.0",
"Creative Commons Attribution Share Alike 2.5 Generic": "CC-BY-SA-2.5",
"Creative Commons Attribution Share Alike 3.0 Unported": "CC-BY-SA-3.0",
"Creative Commons Attribution-Share Alike 3.0 Austria": "CC-BY-SA-3.0-AT",
"Creative Commons Attribution Share Alike 4.0 International": "CC-BY-SA-4.0",
"Creative Commons Public Domain Dedication and Certification": "CC-PDDC",
"Creative Commons Zero v1.0 Universal": "CC0-1.0",
"Common Development and Distribution License 1.0": "CDDL-1.0",
"Common Development and Distribution License 1.1": "CDDL-1.1",
"Community Data License Agreement Permissive 1.0": "CDLA-Permissive-1.0",
"Community Data License Agreement Sharing 1.0": "CDLA-Sharing-1.0",
"CeCILL Free Software License Agreement v1.0": "CECILL-1.0",
"CeCILL Free Software License Agreement v1.1": "CECILL-1.1",
"CeCILL Free Software License Agreement v2.0": "CECILL-2.0",
"CeCILL Free Software License Agreement v2.1": "CECILL-2.1",
"CeCILL-B Free Software License Agreement": "CECILL-B",
"CeCILL-C Free Software License Agreement": "CECILL-C",
"CERN Open Hardware Licence v1.1": "CERN-OHL-1.1",
"CERN Open Hardware Licence v1.2": "CERN-OHL-1.2",
"CERN Open Hardware Licence Version 2 - Permissive": "CERN-OHL-P-2.0",
"CERN Open Hardware Licence Version 2 - Strongly Reciprocal": "CERN-OHL-S-2.0",
"CERN Open Hardware Licence Version 2 - Weakly Reciprocal": "CERN-OHL-W-2.0",
"Clarified Artistic License": "ClArtistic",
"CNRI Jython License": "CNRI-Jython",
"CNRI Python License": "CNRI-Python",
"CNRI Python Open Source GPL Compatible License Agreement": "CNRI-Python-GPL-Compatible",
"Condor Public License v1.1": "Condor-1.1",
"copyleft-next 0.3.0": "copyleft-next-0.3.0",
"copyleft-next 0.3.1": "copyleft-next-0.3.1",
"Common Public Attribution License 1.0": "CPAL-1.0",
"Common Public License 1.0": "CPL-1.0",
"Code Project Open License 1.02": "CPOL-1.02",
"Crossword License": "Crossword",
"CrystalStacker License": "CrystalStacker",
"CUA Office Public License v1.0": "CUA-OPL-1.0",
"Cube License": "Cube",
"curl License": "curl",
"Deutsche Freie Software Lizenz": "D-FSL-1.0",
"diffmark license": "diffmark",
"DOC License": "DOC",
"Dotseqn License": "Dotseqn",
"DSDP License": "DSDP",
"dvipdfm License": "dvipdfm",
"Educational Community License v1.0": "ECL-1.0",
"Educational Community License v2.0": "ECL-2.0",
"Eiffel Forum License v1.0": "EFL-1.0",
"Eiffel Forum License v2.0": "EFL-2.0",
"eGenix.com Public License 1.1.0": "eGenix",
"Entessa Public License v1.0": "Entessa",
"EPICS Open License": "EPICS",
"Eclipse Public License 1.0": "EPL-1.0",
"Eclipse Public License 2.0": "EPL-2.0",
"Erlang Public License v1.1": "ErlPL-1.1",
"Etalab Open License 2.0": "etalab-2.0",
"EU DataGrid Software License": "EUDatagrid",
"European Union Public License 1.0": "EUPL-1.0",
"European Union Public License 1.1": "EUPL-1.1",
"European Union Public License 1.2": "EUPL-1.2",
"Eurosym License": "Eurosym",
"Fair License": "Fair",
"Frameworx Open License 1.0": "Frameworx-1.0",
"FreeImage Public License v1.0": "FreeImage",
"FSF All Permissive License": "FSFAP",
"FSF Unlimited License": "FSFUL",
"FSF Unlimited License (with License Retention)": "FSFULLR",
"Freetype Project License": "FTL",
"GNU Free Documentation License v1.1 only - invariants": "GFDL-1.1-invariants-only",
"GNU Free Documentation License v1.1 or later - invariants": "GFDL-1.1-invariants-or-later",
"GNU Free Documentation License v1.1 only - no invariants": "GFDL-1.1-no-invariants-only",
"GNU Free Documentation License v1.1 or later - no invariants": "GFDL-1.1-no-invariants-or-later",
"GNU Free Documentation License v1.1 only": "GFDL-1.1-only",
"GNU Free Documentation License v1.1 or later": "GFDL-1.1-or-later",
"GNU Free Documentation License v1.2 only - invariants": "GFDL-1.2-invariants-only",
"GNU Free Documentation License v1.2 or later - invariants": "GFDL-1.2-invariants-or-later",
"GNU Free Documentation License v1.2 only - no invariants": "GFDL-1.2-no-invariants-only",
"GNU Free Documentation License v1.2 or later - no invariants": "GFDL-1.2-no-invariants-or-later",
"GNU Free Documentation License v1.2 only": "GFDL-1.2-only",
"GNU Free Documentation License v1.2 or later": "GFDL-1.2-or-later",
"GNU Free Documentation License v1.3 only - invariants": "GFDL-1.3-invariants-only",
"GNU Free Documentation License v1.3 or later - invariants": "GFDL-1.3-invariants-or-later",
"GNU Free Documentation License v1.3 only - no invariants": "GFDL-1.3-no-invariants-only",
"GNU Free Documentation License v1.3 or later - no invariants": "GFDL-1.3-no-invariants-or-later",
"GNU Free Documentation License v1.3 only": "GFDL-1.3-only",
"GNU Free Documentation License v1.3 or later": "GFDL-1.3-or-later",
"Giftware License": "Giftware",
"GL2PS License": "GL2PS",
"3dfx Glide License": "Glide",
"Glulxe License": "Glulxe",
"Good Luck With That Public License": "GLWTPL",
"gnuplot License": "gnuplot",
"GNU General Public License v1.0 only": "GPL-1.0-only",
"GNU General Public License v1.0 or later": "GPL-1.0-or-later",
"GNU General Public License v2.0 only": "GPL-2.0-only",
"GNU General Public License v2.0 or later": "GPL-2.0-or-later",
"GNU General Public License v3.0 only": "GPL-3.0-only",
"GNU General Public License v3.0 or later": "GPL-3.0-or-later",
"gSOAP Public License v1.3b": "gSOAP-1.3b",
"Haskell Language Report License": "HaskellReport",
"Hippocratic License 2.1": "Hippocratic-2.1",
"Historical Permission Notice and Disclaimer": "HPND",
"Historical Permission Notice and Disclaimer - sell variant": "HPND-sell-variant",
"IBM PowerPC Initialization and Boot Software": "IBM-pibs",
"ICU License": "ICU",
"Independent JPEG Group License": "IJG",
"ImageMagick License": "ImageMagick",
"iMatix Standard Function Library Agreement": "iMatix",
"Imlib2 License": "Imlib2",
"Info-ZIP License": "Info-ZIP",
"Intel Open Source License": "Intel",
"Intel ACPI Software License Agreement": "Intel-ACPI",
"Interbase Public License v1.0": "Interbase-1.0",
"IPA Font License": "IPA",
"IBM Public License v1.0": "IPL-1.0",
"ISC License": "ISC",
"JasPer License": "JasPer-2.0",
"Japan Network Information Center License": "JPNIC",
"JSON License": "JSON",
"Licence Art Libre 1.2": "LAL-1.2",
"Licence Art Libre 1.3": "LAL-1.3",
"Latex2e License": "Latex2e",
"Leptonica License": "Leptonica",
"GNU Library General Public License v2 only": "LGPL-2.0-only",
"GNU Library General Public License v2 or later": "LGPL-2.0-or-later",
"GNU Lesser General Public License v2.1 only": "LGPL-2.1-only",
"GNU Lesser General Public License v2.1 or later": "LGPL-2.1-or-later",
"GNU Lesser General Public License v3.0 only": "LGPL-3.0-only",
"GNU Lesser General Public License v3.0 or later": "LGPL-3.0-or-later",
"Lesser General Public License For Linguistic Resources": "LGPLLR",
"libpng License": "Libpng",
"PNG Reference Library version 2": "libpng-2.0",
"libselinux public domain notice": "libselinux-1.0",
"libtiff License": "libtiff",
"Licence Libre du Québec – Permissive version 1.1": "LiLiQ-P-1.1",
"Licence Libre du Québec – Réciprocité version 1.1": "LiLiQ-R-1.1",
"Licence Libre du Québec – Réciprocité forte version 1.1": "LiLiQ-Rplus-1.1",
"Linux Kernel Variant of OpenIB.org license": "Linux-OpenIB",
"Lucent Public License Version 1.0": "LPL-1.0",
"Lucent Public License v1.02": "LPL-1.02",
"LaTeX Project Public License v1.0": "LPPL-1.0",
"LaTeX Project Public License v1.1": "LPPL-1.1",
"LaTeX Project Public License v1.2": "LPPL-1.2",
"LaTeX Project Public License v1.3a": "LPPL-1.3a",
"LaTeX Project Public License v1.3c": "LPPL-1.3c",
"MakeIndex License": "MakeIndex",
"The MirOS Licence": "MirOS",
"MIT License": "MIT",
"MIT No Attribution": "MIT-0",
"Enlightenment License (e16)": "MIT-advertising",
"CMU License": "MIT-CMU",
"enna License": "MIT-enna",
"feh License": "MIT-feh",
"MIT +no-false-attribs license": "MITNFA",
"Motosoto License": "Motosoto",
"mpich2 License": "mpich2",
"Mozilla Public License 1.0": "MPL-1.0",
"Mozilla Public License 1.1": "MPL-1.1",
"Mozilla Public License 2.0": "MPL-2.0",
"Mozilla Public License 2.0 (no copyleft exception)": "MPL-2.0-no-copyleft-exception",
"Microsoft Public License": "MS-PL",
"Microsoft Reciprocal License": "MS-RL",
"Matrix Template Library License": "MTLL",
"Mulan Permissive Software License, Version 1": "MulanPSL-1.0",
"Mulan Permissive Software License, Version 2": "MulanPSL-2.0",
"Multics License": "Multics",
"Mup License": "Mup",
"NASA Open Source Agreement 1.3": "NASA-1.3",
"Naumen Public License": "Naumen",
"Net Boolean Public License v1": "NBPL-1.0",
"Non-Commercial Government Licence": "NCGL-UK-2.0",
"University of Illinois/NCSA Open Source License": "NCSA",
"Net-SNMP License": "Net-SNMP",
"NetCDF license": "NetCDF",
"Newsletr License": "Newsletr",
"Nethack General Public License": "NGPL",
"NIST Public Domain Notice": "NIST-PD",
"NIST Public Domain Notice with license fallback": "NIST-PD-fallback",
"Norwegian Licence for Open Government Data": "NLOD-1.0",
"No Limit Public License": "NLPL",
"Nokia Open Source License": "Nokia",
"Netizen Open Source License": "NOSL",
"Noweb License": "Noweb",
"Netscape Public License v1.0": "NPL-1.0",
"Netscape Public License v1.1": "NPL-1.1",
"Non-Profit Open Software License 3.0": "NPOSL-3.0",
"NRL License": "NRL",
"NTP License": "NTP",
"NTP No Attribution": "NTP-0",
"Open Use of Data Agreement v1.0": "O-UDA-1.0",
"Open CASCADE Technology Public License": "OCCT-PL",
"OCLC Research Public License 2.0": "OCLC-2.0",
"ODC Open Database License v1.0": "ODbL-1.0",
"Open Data Commons Attribution License v1.0": "ODC-By-1.0",
"SIL Open Font License 1.0": "OFL-1.0",
"SIL Open Font License 1.0 with no Reserved Font Name": "OFL-1.0-no-RFN",
"SIL Open Font License 1.0 with Reserved Font Name": "OFL-1.0-RFN",
"SIL Open Font License 1.1": "OFL-1.1",
"SIL Open Font License 1.1 with no Reserved Font Name": "OFL-1.1-no-RFN",
"SIL Open Font License 1.1 with Reserved Font Name": "OFL-1.1-RFN",
"OGC Software License, Version 1.0": "OGC-1.0",
"Open Government Licence - Canada": "OGL-Canada-2.0",
"Open Government Licence v1.0": "OGL-UK-1.0",
"Open Government Licence v2.0": "OGL-UK-2.0",
"Open Government Licence v3.0": "OGL-UK-3.0",
"Open Group Test Suite License": "OGTSL",
"Open LDAP Public License v1.1": "OLDAP-1.1",
"Open LDAP Public License v1.2": "OLDAP-1.2",
"Open LDAP Public License v1.3": "OLDAP-1.3",
"Open LDAP Public License v1.4": "OLDAP-1.4",
"Open LDAP Public License v2.0 (or possibly 2.0A and 2.0B)": "OLDAP-2.0",
"Open LDAP Public License v2.0.1": "OLDAP-2.0.1",
"Open LDAP Public License v2.1": "OLDAP-2.1",
"Open LDAP Public License v2.2": "OLDAP-2.2",
"Open LDAP Public License v2.2.1": "OLDAP-2.2.1",
"Open LDAP Public License 2.2.2": "OLDAP-2.2.2",
"Open LDAP Public License v2.3": "OLDAP-2.3",
"Open LDAP Public License v2.4": "OLDAP-2.4",
"Open LDAP Public License v2.5": "OLDAP-2.5",
"Open LDAP Public License v2.6": "OLDAP-2.6",
"Open LDAP Public License v2.7": "OLDAP-2.7",
"Open LDAP Public License v2.8": "OLDAP-2.8",
"Open Market License": "OML",
"OpenSSL License": "OpenSSL",
"Open Public License v1.0": "OPL-1.0",
"OSET Public License version 2.1": "OSET-PL-2.1",
"Open Software License 1.0": "OSL-1.0",
"Open Software License 1.1": "OSL-1.1",
"Open Software License 2.0": "OSL-2.0",
"Open Software License 2.1": "OSL-2.1",
"Open Software License 3.0": "OSL-3.0",
"The Parity Public License 6.0.0": "Parity-6.0.0",
"The Parity Public License 7.0.0": "Parity-7.0.0",
"ODC Public Domain Dedication & License 1.0": "PDDL-1.0",
"PHP License v3.0": "PHP-3.0",
"PHP License v3.01": "PHP-3.01",
"Plexus Classworlds License": "Plexus",
"PolyForm Noncommercial License 1.0.0": "PolyForm-Noncommercial-1.0.0",
"PolyForm Small Business License 1.0.0": "PolyForm-Small-Business-1.0.0",
"PostgreSQL License": "PostgreSQL",
"Python Software Foundation License 2.0": "PSF-2.0",
"psfrag License": "psfrag",
"psutils License": "psutils",
"Python License 2.0": "Python-2.0",
"Qhull License": "Qhull",
"Q Public License 1.0": "QPL-1.0",
"Rdisc License": "Rdisc",
"Red Hat eCos Public License v1.1": "RHeCos-1.1",
"Reciprocal Public License 1.1": "RPL-1.1",
"Reciprocal Public License 1.5": "RPL-1.5",
"RealNetworks Public Source License v1.0": "RPSL-1.0",
"RSA Message-Digest License": "RSA-MD",
"Ricoh Source Code Public License": "RSCPL",
"Ruby License": "Ruby",
"Sax Public Domain Notice": "SAX-PD",
"Saxpath License": "Saxpath",
"SCEA Shared Source License": "SCEA",
"Sendmail License": "Sendmail",
"Sendmail License 8.23": "Sendmail-8.23",
"SGI Free Software License B v1.0": "SGI-B-1.0",
"SGI Free Software License B v1.1": "SGI-B-1.1",
"SGI Free Software License B v2.0": "SGI-B-2.0",
"Solderpad Hardware License v0.5": "SHL-0.5",
"Solderpad Hardware License, Version 0.51": "SHL-0.51",
"Simple Public License 2.0": "SimPL-2.0",
"Sun Industry Standards Source License v1.1": "SISSL",
"Sun Industry Standards Source License v1.2": "SISSL-1.2",
"Sleepycat License": "Sleepycat",
"Standard ML of New Jersey License": "SMLNJ",
"Secure Messaging Protocol Public License": "SMPPL",
"SNIA Public License 1.1": "SNIA",
"Spencer License 86": "Spencer-86",
"Spencer License 94": "Spencer-94",
"Spencer License 99": "Spencer-99",
"Sun Public License v1.0": "SPL-1.0",
"SSH OpenSSH license": "SSH-OpenSSH",
"SSH short notice": "SSH-short",
"Server Side Public License, v 1": "SSPL-1.0",
"SugarCRM Public License v1.1.3": "SugarCRM-1.1.3",
"Scheme Widget Library (SWL) Software License Agreement": "SWL",
"TAPR Open Hardware License v1.0": "TAPR-OHL-1.0",
"TCL/TK License": "TCL",
"TCP Wrappers License": "TCP-wrappers",
"TMate Open Source License": "TMate",
"TORQUE v2.5+ Software License v1.1": "TORQUE-1.1",
"Trusster Open Source License": "TOSL",
"Technische Universitaet Berlin License 1.0": "TU-Berlin-1.0",
"Technische Universitaet Berlin License 2.0": "TU-Berlin-2.0",
"Upstream Compatibility License v1.0": "UCL-1.0",
"Unicode License Agreement - Data Files and Software (2015)": "Unicode-DFS-2015",
"Unicode License Agreement - Data Files and Software (2016)": "Unicode-DFS-2016",
"Unicode Terms of Use": "Unicode-TOU",
"The Unlicense": "Unlicense",
"Universal Permissive License v1.0": "UPL-1.0",
"Vim License": "Vim",
"VOSTROM Public License for Open Source": "VOSTROM",
"Vovida Software License v1.0": "VSL-1.0",
"W3C Software Notice and License (2002-12-31)": "W3C",
"W3C Software Notice and License (1998-07-20)": "W3C-19980720",
"W3C Software Notice and Document License (2015-05-13)": "W3C-20150513",
"Sybase Open Watcom Public License 1.0": "Watcom-1.0",
"Wsuipa License": "Wsuipa",
"Do What The F*ck You Want To Public License": "WTFPL",
"X11 License": "X11",
"Xerox License": "Xerox",
"XFree86 License 1.1": "XFree86-1.1",
"xinetd License": "xinetd",
"X.Net License": "Xnet",
"XPP License": "xpp",
"XSkat License": "XSkat",
"Yahoo! Public License v1.0": "YPL-1.0",
"Yahoo! Public License v1.1": "YPL-1.1",
"Zed License": "Zed",
"Zend License v2.0": "Zend-2.0",
"Zimbra Public License v1.3": "Zimbra-1.3",
"Zimbra Public License v1.4": "Zimbra-1.4",
"zlib License": "Zlib",
"zlib/libpng License with Acknowledgement": "zlib-acknowledgement",
"Zope Public License 1.1": "ZPL-1.1",
"Zope Public License 2.0": "ZPL-2.0",
"Zope Public License 2.1": "ZPL-2.1" }

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
parser.add_argument("version", type=str, help='Black Duck version name')
parser.add_argument("-o", "--output", type=str, help="Output SPDX file name (SPDX tag format) - default '<proj>-<ver>.spdx'", default="")
parser.add_argument("-r", "--recursive", help="Scan sub-projects within projects",action='store_true')

args = parser.parse_args()

def clean(name):
	remove_chars = [';', ':', '!', "*", "(", ")", "/", ","]
	for i in remove_chars :
		name = name.replace(i, '')
	replace_chars = [' ', '.']
	for i in replace_chars :
		name = name.replace(i, '-')
	return(name)

if args.output == "":
	args.output = clean(args.project_name) + "-" + clean(args.version) + ".spdx"

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


# from xml.dom import minidom
# def get_nvd_cpes():
# 	items = []
#
# 	cpe_xml_url = "https://nvd.nist.gov/feeds/xml/cpe/dictionary/official-cpe-dictionary_v2.3.xml.zip"
# 	cpe_xml_file = "official-cpe-dictionary_v2.3.xml"
# 	if not os.path.exists(cpe_xml_file):
# 		try:
# 			print("Downloading CPE Dictionary from nvd.nist.gov ... ", end="", flush=True)
# 			cpe_zip = requests.get(cpe_xml_url)
# 			with open(cpe_xml_file + ".zip", 'wb') as f:
# 				f.write(cpe_zip.content)
# 			print("Done")
#
# 			print("Extracting CPE Dictionary ... ", end = '', flush=True)
# 			zf = ZipFile(cpe_xml_file + ".zip", 'r')
# 			zf.extractall()
# 			zf.close()
# 			print("Done")
# 		except:
# 			print("Unable to download CPE dictionary - will continue without CPE processing")
# 			return([])
# 	else:
# 		print("CPE dictionary file ({}) found in current folder - please check it is up to date".format(cpe_xml_file))
#
# 	print("Processing CPE dictionary ... ", end="", flush=True)
# 	try:
# 		mydoc = minidom.parse(cpe_xml_file)
#
# 		items = mydoc.getElementsByTagName('cpe-item')
# 		print("Processed {} items\n".format(len(items)))
#
# 	except:
# 		print("ERROR")
# 		return([])
#
# 	return(items)
#
# cpe_items = get_nvd_cpes()
#
# print(cpe_items[2].attributes['name'].value)

hub = HubInstance()

project = hub.get_project_by_name(args.project_name)
if project == None:
	print("Project '{}' does not exist".format(args.project_name))
	list_projects(args.project_name)
	sys.exit(2)

version = hub.get_version_by_name(project, args.version)
if version == None:
	print("Version '{}' does not exist".format(args.version))
	list_versions(args.version)
	sys.exit(2)
else:
	print("Working on project '{}' version '{}'\n".format(args.project_name, args.version))

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

# Get project version info
lic_string = "NOASSERTION"
try:
	quotes = False
	for lic in version['license']['licenses']:
		if lic['name'] == "Unknown License":
			continue
		if lic['name'] in lic_dict.keys():
			if lic_string == "NOASSERTION":
				lic_string = lic_dict[lic['name']]
			else:
				quotes = True
				lic_string += " AND " + lic_dict[lic['name']]
	if quotes:
		lic_string = "(" + lic_string + ")"
except:
	pass

top_package_name = clean("SPDXRef-" + project['name'])

try:
# if True:
	spdx = [ "SPDXVersion: SPDX-2.2",
		"DataLicense: CC0-1.0",
		"# DocumentNamespace: http://spdx.org/spdxdocs/spdx-example-444504E0-4F89-41D3-9A0C-0305E82C3301",
		"DocumentName: SPDX-Project-" + clean(project['name']),
		"",
		"## Black Duck Project",
		"SPDXID: SPDXRef-DOCUMENT",
		"DocumentComment: <text>This document was created by Black Duck</text>",
		"## External Document References",
		"# ExternalDocumentRef: DocumentRef-spdx-tool-1.2 http://spdx.org/spdxdocs/spdx-tools-v1.2-3F2504E0-4F89-41D3-9A0C-0305E82C3301 SHA1: d6a770ba38583ed4bb4525bd96e50461655d2759",
		"## Creation Information",
		"Creator: Tool: Black Duck",
		"# Creator: Organization: ExampleCodeInspect ()",
		"Creator: Person: " + version['createdBy'] ,
		"Created: " + version['createdAt'].split('.')[0] + 'Z',
		"# CreatorComment:",
		"## Annotations",
		"# Annotator: Person: Joe Reviewer",
		"# AnnotationDate: 2010-02-10T00:00:00Z",
		"# AnnotationComment: <text>This is just an example.  Some of the non-standard licenses look like they are actually BSD 3 clause licenses</text>",
		"# AnnotationType: REVIEW",
		"# SPDXREF: SPDXRef-DOCUMENT",
		"## Relationships",
		"Relationship: SPDXRef-DOCUMENT CONTAINS SPDXRef-Package",
		"Relationship: SPDXRef-DOCUMENT DESCRIBES SPDXRef-Package",
		"",
		"PackageName: " + project['name'],
		"SPDXID: SPDXRef-Package",
		"PackageVersion: " + version['versionName'],
		# PackageFileName: glibc-2.11.1.tar.gz
		# PackageSupplier: Person: Jane Doe (jane.doe@example.com)
		# PackageOriginator: Organization: ExampleCodeInspect (contact@example.com)
		# PackageDownloadLocation: http://ftp.gnu.org/gnu/glibc/glibc-ports-2.15.tar.gz
		# PackageVerificationCode: d6a770ba38583ed4bb4525bd96e50461655d2758(excludes: ./package.spdx)
		# PackageChecksum: MD5: 624c1abb3664f4b35547e7c73864ad24
		# PackageChecksum: SHA1: 85ed0817af83a24ad8da68c2b5094de69833983c
		# PackageChecksum: SHA256: 11b6d3ee554eedf79299905a98f9b9a04e498210b59f15094c916c91d150efcd
		# PackageHomePage: http://ftp.gnu.org/gnu/glibc
		# PackageSourceInfo: <text>uses glibc-2_11-branch from git://sourceware.org/git/glibc.git.</text>
		"PackageLicenseConcluded: " + lic_string,
		# ## License information from files
		# PackageLicenseInfoFromFiles: GPL-2.0-only
		# PackageLicenseInfoFromFiles: LicenseRef-1
		# PackageLicenseInfoFromFiles: LicenseRef-2
		"PackageLicenseDeclared: " + lic_string,
		# PackageLicenseComments: <text>The license for this project changed with the release of version x.y.  The version of the project included here post-dates the license change.</text>
		# PackageCopyrightText: <text>Copyright 2008-2010 John Smith</text>
		# PackageSummary: <text></text>",
		# PackageAttributionText: <text>The GNU C Library is free software.  See the file COPYING.LIB for copying conditions, and LICENSES for notices about a few contributions that require these additional notices to be distributed.  License copyright years may be listed using range notation, e.g., 1996-2015, indicating that every year in the range, inclusive, is a copyrightable year that would otherwise be listed individually.</text>
		# ExternalRef: OTHER LocationRef-acmeforge acmecorp/acmenator/4.1.3-alpha
		# ExternalRefComment: This is the external ref for Acme
		# ExternalRef: SECURITY cpe23Type cpe:2.3:a:pivotal_software:spring_framework:4.1.0:*:*:*:*:*:*:*
		# ## Annotations
		# Annotator: Person: Package Commenter
		# AnnotationDate: 2011-01-29T18:30:22Z
		# AnnotationComment: <text>Package level annotation</text>
		# AnnotationType: OTHER
		# SPDXREF: SPDXRef-Package
		""
		]
	if 'description' in project.keys():
		spdx.append("PackageDescription: <text>" + project['description'] + "</text>")

	spdx.append("## Relationships")

except Exception as e:
	print('ERROR: Unable to create spdx header\n' + str(e))
	sys.exit(2)

packages = []
spdx_rels = []

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

spdx_custom_lics_text = []
spdx_custom_lics = []

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
		print("	INFO: No copyrights available due to no assigned origin")
	return(copyrights, cpe)

def get_comments(comp):
	# Get comments/annotations
	hrefs = comp['_meta']['links']
	annotations = ""

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
	return(annotations)

def proc_components(bom_components):
	global packages, spdx

	for bom_component in bom_components['items']:

		#DEBUG
# 		if 'jackson-datatype-joda' not in bom_component['componentName']:
# 			continue

		print(" - " + bom_component['componentName'] + "/" + bom_component['componentVersionName'])
# 		print(json.dumps(bom_component, indent=4))
# 		print("-----------------------------------------------------------------------------------------------------------")

		if 'componentVersionName' not in bom_component.keys():
			print("INFO: Skipping component {} which has no assigned version".format(bom_component['componentName']))
			continue

		spdxpackage_name = clean("SPDX-Package-" + bom_component['componentName'] + "-" + bom_component['componentVersionName'])

		# First check if this component is a sub-project
		if args.recursive:
			if bom_component['matchTypes'][0] == "MANUAL_BOM_COMPONENT" and bom_component['componentName'] in proj_list:
				sub_project = hub.get_project_by_name(bom_component['componentName'])
				if sub_project != "" and sub_project != None:
					sub_version = hub.get_version_by_name(sub_project, bom_component['componentVersionName'])
					if sub_version != "" and sub_version != None:
						print("Processing project within project '{}'".format(bom_component['componentName']))
						sub_bom_components = hub.get_version_components(sub_version)
						proc_components(sub_bom_components)
						continue

		# Get component info
		comp = bom_component['component']
		custom_headers = {'Accept':'application/vnd.blackducksoftware.component-detail-5+json'}
		resp = hub.execute_get(comp, custom_headers=custom_headers)
		kb_component = resp.json()
		openhub_url = next((item for item in kb_component['_meta']['links'] if item["rel"] == "openhub"), None)
		#print(openhub_url['href'])
		if openhub_url != None:
			download_url = openhub_get_download(openhub_url['href'])
		else:
			download_url = "NOASSERTION"

		annotations = get_comments(bom_component)

		lic_string = get_licenses(bom_component)

		copyrights, cpe = get_orig_data(bom_component)

		try:
			this_package = [
				"## Black Duck project component",
				"PackageName: " + bom_component['componentName'],
				"SPDXID: " + spdxpackage_name,
				"PackageVersion: " + bom_component['componentVersionName'],
				# PackageFileName: saxonB-8.8.zip
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

		spdx.append("Relationship: SPDXRef-Package CONTAINS " + spdxpackage_name)

		if 'description' in kb_component.keys():
			this_package += "PackageDescription: <text>" + kb_component['description'] + "</text>",
		this_package += [ "PackageCopyrightText: <text>", copyrights, "</text>", annotations ]

		packages.extend(this_package)

print("Processing components:")
proc_components(bom_components)

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

##########################################################################################
# SPDXVersion: SPDX-2.2
# DataLicense: CC0-1.0
# DocumentNamespace: http://spdx.org/spdxdocs/spdx-example-444504E0-4F89-41D3-9A0C-0305E82C3301
# DocumentName: SPDX-Tools-v2.0
# SPDXID: SPDXRef-DOCUMENT
# DocumentComment: <text>This document was created using SPDX 2.0 using licenses from the web site.</text>
#
# ## External Document References
# ExternalDocumentRef: DocumentRef-spdx-tool-1.2 http://spdx.org/spdxdocs/spdx-tools-v1.2-3F2504E0-4F89-41D3-9A0C-0305E82C3301 SHA1: d6a770ba38583ed4bb4525bd96e50461655d2759
# ## Creation Information
# Creator: Tool: LicenseFind-1.0
# Creator: Organization: ExampleCodeInspect ()
# Creator: Person: Jane Doe ()
# Created: 2010-01-29T18:30:22Z
# CreatorComment: <text>This package has been shipped in source and binary form.
# The binaries were created with gcc 4.5.1 and expect to link to
# compatible system run time libraries.</text>
# LicenseListVersion: 3.9
# ## Annotations
# Annotator: Person: Joe Reviewer
# AnnotationDate: 2010-02-10T00:00:00Z
# AnnotationComment: <text>This is just an example.  Some of the non-standard licenses look like they are actually BSD 3 clause licenses</text>
# AnnotationType: REVIEW
# SPDXREF: SPDXRef-DOCUMENT
# Annotator: Person: Suzanne Reviewer
# AnnotationDate: 2011-03-13T00:00:00Z
# AnnotationComment: <text>Another example reviewer.</text>
# AnnotationType: REVIEW
# SPDXREF: SPDXRef-DOCUMENT
# Annotator: Person: Jane Doe ()
# AnnotationDate: 2010-01-29T18:30:22Z
# AnnotationComment: <text>Document level annotation</text>
# AnnotationType: OTHER
# SPDXREF: SPDXRef-DOCUMENT
# ## Relationships
# Relationship: SPDXRef-DOCUMENT CONTAINS SPDXRef-Package
# Relationship: SPDXRef-DOCUMENT COPY_OF DocumentRef-spdx-tool-1.2:SPDXRef-ToolsElement
# Relationship: SPDXRef-DOCUMENT DESCRIBES SPDXRef-Package
# Relationship: SPDXRef-DOCUMENT DESCRIBES SPDXRef-File
#
# FileName: ./package/foo.c
# SPDXID: SPDXRef-File
# FileComment: <text>The concluded license was taken from the package level that the file was included in.
# This information was found in the COPYING.txt file in the xyz directory.</text>
# FileType: SOURCE
# FileChecksum: SHA1: d6a770ba38583ed4bb4525bd96e50461655d2758
# FileChecksum: MD5: 624c1abb3664f4b35547e7c73864ad24
# LicenseConcluded: (LGPL-2.0-only OR LicenseRef-2)
# LicenseInfoInFile: LicenseRef-2
# LicenseInfoInFile: GPL-2.0-only
# LicenseComments: The concluded license was taken from the package level that the file was included in.
# FileCopyrightText: <text>Copyright 2008-2010 John Smith</text>
# FileNotice: <text>Copyright (c) 2001 Aaron Lehmann aaroni@vitelus.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the �Software�), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED �AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.</text>
# FileContributor: The Regents of the University of California
# FileContributor: Modified by Paul Mundt lethal@linux-sh.org
# FileContributor: IBM Corporation
# ## Annotations
# Annotator: Person: File Commenter
# AnnotationDate: 2011-01-29T18:30:22Z
# AnnotationComment: <text>File level annotation</text>
# AnnotationType: OTHER
# SPDXREF: SPDXRef-File
# ## Relationships
# Relationship: SPDXRef-File GENERATED_FROM SPDXRef-fromDoap-0
# ## Package Information
# PackageName: glibc
# SPDXID: SPDXRef-Package
# PackageVersion: 2.11.1
# PackageFileName: glibc-2.11.1.tar.gz
# PackageSupplier: Person: Jane Doe (jane.doe@example.com)
# PackageOriginator: Organization: ExampleCodeInspect (contact@example.com)
# PackageDownloadLocation: http://ftp.gnu.org/gnu/glibc/glibc-ports-2.15.tar.gz
# PackageVerificationCode: d6a770ba38583ed4bb4525bd96e50461655d2758(excludes: ./package.spdx)
# PackageChecksum: MD5: 624c1abb3664f4b35547e7c73864ad24
# PackageChecksum: SHA1: 85ed0817af83a24ad8da68c2b5094de69833983c
# PackageChecksum: SHA256: 11b6d3ee554eedf79299905a98f9b9a04e498210b59f15094c916c91d150efcd
# PackageHomePage: http://ftp.gnu.org/gnu/glibc
# PackageSourceInfo: <text>uses glibc-2_11-branch from git://sourceware.org/git/glibc.git.</text>
# PackageLicenseConcluded: (LicenseRef-3 OR LGPL-2.0-only)
# ## License information from files
# PackageLicenseInfoFromFiles: GPL-2.0-only
# PackageLicenseInfoFromFiles: LicenseRef-1
# PackageLicenseInfoFromFiles: LicenseRef-2
# PackageLicenseDeclared: (LicenseRef-3 AND LGPL-2.0-only)
# PackageLicenseComments: <text>The license for this project changed with the release of version x.y.  The version of the project included here post-dates the license change.</text>
# PackageCopyrightText: <text>Copyright 2008-2010 John Smith</text>
# PackageSummary: <text>GNU C library.</text>
# PackageDescription: <text>The GNU C Library defines functions that are specified by the ISO C standard, as well as additional features specific to POSIX and other derivatives of the Unix operating system, and extensions specific to GNU systems.</text>
# PackageAttributionText: <text>The GNU C Library is free software.  See the file COPYING.LIB for copying conditions, and LICENSES for notices about a few contributions that require these additional notices to be distributed.  License copyright years may be listed using range notation, e.g., 1996-2015, indicating that every year in the range, inclusive, is a copyrightable year that would otherwise be listed individually.</text>
# ExternalRef: OTHER LocationRef-acmeforge acmecorp/acmenator/4.1.3-alpha
# ExternalRefComment: This is the external ref for Acme
# ExternalRef: SECURITY cpe23Type cpe:2.3:a:pivotal_software:spring_framework:4.1.0:*:*:*:*:*:*:*
# ## Annotations
# Annotator: Person: Package Commenter
# AnnotationDate: 2011-01-29T18:30:22Z
# AnnotationComment: <text>Package level annotation</text>
# AnnotationType: OTHER
# SPDXREF: SPDXRef-Package
# ## Relationships
# Relationship: SPDXRef-Package CONTAINS SPDXRef-JenaLib
# Relationship: SPDXRef-Package DYNAMIC_LINK SPDXRef-Saxon
#
# ## File Information
# FileName: ./lib-source/commons-lang3-3.1-sources.jar
# SPDXID: SPDXRef-CommonsLangSrc
# FileComment: <text>This file is used by Jena</text>
# FileType: ARCHIVE
# FileChecksum: SHA1: c2b4e1c67a2d28fced849ee1bb76e7391b93f125
# LicenseConcluded: Apache-2.0
# LicenseInfoInFile: Apache-2.0
# FileCopyrightText: <text>Copyright 2001-2011 The Apache Software Foundation</text>
# FileNotice: <text>Apache Commons Lang
# Copyright 2001-2011 The Apache Software Foundation
#
# This product includes software developed by
# The Apache Software Foundation (http://www.apache.org/).
#
# This product includes software from the Spring Framework,
# under the Apache License 2.0 (see: StringUtils.containsWhitespace())</text>
# FileContributor: Apache Software Foundation
# ## Relationships
# Relationship: SPDXRef-CommonsLangSrc GENERATED_FROM NOASSERTION
#
# FileName: ./lib-source/jena-2.6.3-sources.jar
# SPDXID: SPDXRef-JenaLib
# FileComment: <text>This file belongs to Jena</text>
# FileType: ARCHIVE
# FileChecksum: SHA1: 3ab4e1c67a2d28fced849ee1bb76e7391b93f125
# LicenseConcluded: LicenseRef-1
# LicenseInfoInFile: LicenseRef-1
# LicenseComments: This license is used by Jena
# FileCopyrightText: <text>(c) Copyright 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009 Hewlett-Packard Development Company, LP</text>
# FileContributor: Hewlett Packard Inc.
# FileContributor: Apache Software Foundation
# FileDependency: ./lib-source/commons-lang3-3.1-sources.jar
# ## Relationships
# Relationship: SPDXRef-JenaLib CONTAINS SPDXRef-Package
#
# FileName: ./src/org/spdx/parser/DOAPProject.java
# SPDXID: SPDXRef-DoapSource
# FileType: SOURCE
# FileChecksum: SHA1: 2fd4e1c67a2d28fced849ee1bb76e7391b93eb12
# LicenseConcluded: Apache-2.0
# LicenseInfoInFile: Apache-2.0
# FileCopyrightText: <text>Copyright 2010, 2011 Source Auditor Inc.</text>
# FileContributor: Open Logic Inc.
# FileContributor: Black Duck Software In.c
# FileContributor: Source Auditor Inc.
# FileContributor: SPDX Technical Team Members
# FileContributor: Protecode Inc.
# FileDependency: ./lib-source/jena-2.6.3-sources.jar
# FileDependency: ./lib-source/commons-lang3-3.1-sources.jar
#
# ## Package Information
# PackageName: Apache Commons Lang
# SPDXID: SPDXRef-fromDoap-1
# PackageComment: <text>This package was converted from a DOAP Project by the same name</text>
# PackageDownloadLocation: NOASSERTION
# PackageHomePage: http://commons.apache.org/proper/commons-lang/
# PackageLicenseConcluded: NOASSERTION
# PackageLicenseDeclared: NOASSERTION
# PackageCopyrightText: <text>NOASSERTION</text>
# FilesAnalyzed: false
#
# ## Package Information
# PackageName: Jena
# SPDXID: SPDXRef-fromDoap-0
# PackageComment: <text>This package was converted from a DOAP Project by the same name</text>
# PackageDownloadLocation: NOASSERTION
# PackageHomePage: http://www.openjena.org/
# PackageLicenseConcluded: NOASSERTION
# PackageLicenseDeclared: NOASSERTION
# PackageCopyrightText: <text>NOASSERTION</text>
# FilesAnalyzed: false
#
# ## Package Information
# PackageName: Saxon
# SPDXID: SPDXRef-Saxon
# PackageVersion: 8.8
# PackageFileName: saxonB-8.8.zip
# PackageDownloadLocation: https://sourceforge.net/projects/saxon/files/Saxon-B/8.8.0.7/saxonb8-8-0-7j.zip/download
# PackageChecksum: SHA1: 85ed0817af83a24ad8da68c2b5094de69833983c
# PackageHomePage: http://saxon.sourceforge.net/
# PackageLicenseConcluded: MPL-1.0
# PackageLicenseDeclared: MPL-1.0
# PackageLicenseComments: <text>Other versions available for a commercial license</text>
# PackageDescription: <text>The Saxon package is a collection of tools for processing XML documents.</text>
# PackageCopyrightText: <text>Copyright Saxonica Ltd</text>
# FilesAnalyzed: false
#
# ## Snippet Information
# SnippetSPDXID: SPDXRef-Snippet
# SnippetFromFileSPDXID: SPDXRef-DoapSource
# SnippetByteRange: 310:420
# SnippetLineRange: 5:23
# SnippetLicenseConcluded: GPL-2.0-only
# LicenseInfoInSnippet: GPL-2.0-only
# SnippetLicenseComments: The concluded license was taken from package xyz, from which the snippet was copied into the current file. The concluded license information was found in the COPYING.txt file in package xyz.
# SnippetCopyrightText: Copyright 2008-2010 John Smith
# SnippetComment: This snippet was identified as significant and highlighted in this Apache-2.0 file, when a commercial scanner identified it as being derived from file foo.c in package xyz which is licensed under GPL-2.0.
# SnippetName: from linux kernel
#
#
# ## License Information
# LicenseID: LicenseRef-1
# ExtractedText: <text>/*
#  * (c) Copyright 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009 Hewlett-Packard Development Company, LP
#  * All rights reserved.
#  *
#  * Redistribution and use in source and binary forms, with or without
#  * modification, are permitted provided that the following conditions
#  * are met:
#  * 1. Redistributions of source code must retain the above copyright
#  *    notice, this list of conditions and the following disclaimer.
#  * 2. Redistributions in binary form must reproduce the above copyright
#  *    notice, this list of conditions and the following disclaimer in the
#  *    documentation and/or other materials provided with the distribution.
#  * 3. The name of the author may not be used to endorse or promote products
#  *    derived from this software without specific prior written permission.
#  *
#  * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
#  * IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
#  * OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#  * IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
#  * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
#  * NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
#  * THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# */</text>
#
# LicenseID: LicenseRef-2
# ExtractedText: <text>This package includes the GRDDL parser developed by Hewlett Packard under the following license:
# � Copyright 2007 Hewlett-Packard Development Company, LP
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
# The name of the author may not be used to endorse or promote products derived from this software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.</text>
#
# LicenseID: LicenseRef-Beerware-4.2
# ExtractedText: <text>"THE BEER-WARE LICENSE" (Revision 42):
# phk@FreeBSD.ORG wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  </
# LicenseName: Beer-Ware License (Version 42)
# LicenseCrossReference:  http://people.freebsd.org/~phk/
# LicenseComment:
# The beerware license has a couple of other standard variants.</text>
#
# LicenseID: LicenseRef-3
# ExtractedText: <text>The CyberNeko Software License, Version 1.0
#
#
# (C) Copyright 2002-2005, Andy Clark.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# 3. The end-user documentation included with the redistribution,
#    if any, must include the following acknowledgment:
#      "This product includes software developed by Andy Clark."
#    Alternately, this acknowledgment may appear in the software itself,
#    if and wherever such third-party acknowledgments normally appear.
#
# 4. The names "CyberNeko" and "NekoHTML" must not be used to endorse
#    or promote products derived from this software without prior
#    written permission. For written permission, please contact
#    andyc@cyberneko.net.
#
# 5. Products derived from this software may not be called "CyberNeko",
#    nor may "CyberNeko" appear in their name, without prior written
#    permission of the author.
#
# THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESSED OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR OTHER CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.</text>
# LicenseName: CyberNeko License
# LicenseCrossReference: http://people.apache.org/~andyc/neko/LICENSE, http://justasample.url.com
# LicenseComment: <text>This is tye CyperNeko License</text>
#
# LicenseID: LicenseRef-4
# ExtractedText: <text>/*
#  * (c) Copyright 2009 University of Bristol
#  * All rights reserved.
#  *
#  * Redistribution and use in source and binary forms, with or without
#  * modification, are permitted provided that the following conditions
#  * are met:
#  * 1. Redistributions of source code must retain the above copyright
#  *    notice, this list of conditions and the following disclaimer.
#  * 2. Redistributions in binary form must reproduce the above copyright
#  *    notice, this list of conditions and the following disclaimer in the
#  *    documentation and/or other materials provided with the distribution.
#  * 3. The name of the author may not be used to endorse or promote products
#  *    derived from this software without specific prior written permission.
#  *
#  * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
#  * IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
#  * OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#  * IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
#  * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
#  * NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
#  * THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# */</text>
