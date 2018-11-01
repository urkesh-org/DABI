#!/usr/bin/env python3
"""
CerPhaS: Ceramics Digital Book - Shapes by phase/stratum
    Author: bF  ( cerphas@forni.me )
    
"""


import sys
import os
import re
import datetime
import jinja2  # template
from collections import defaultdict

from config import *  # import configuration from "config.py"
# TODO: use different configuration storage

print(os.getcwd())


class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open(LOG, 'w', encoding="utf-8")
        self.log.close()

    def write(self, message):
        self.terminal.write(message)
        self.log = open(LOG, 'a', encoding="utf-8")
        self.log.write(message)
        self.log.close()

    def flush(self):
        pass


def read_all_files(sherds_dir):
    """ Read files in "input_sherds" and return list of sherds """
    
    sherds = []
    
    for file in os.listdir(sherds_dir):
        if not os.path.isfile(SHERDS_DIR + file):  # no folders
            continue
        try:
            with open(SHERDS_DIR + file, 'r') as lines:
                for line in lines:
                    line = line.strip().replace('–', '-')
                    if not line or line.startswith(';'):
                        continue
                    
                    sherds.append(line)
            
            # os.rename(file, "zzDone-"+file)
                    
        except IOError as err1:
            input("[Err]", str(err1))
            sys.exit()
        except UnicodeError:
            input(f"[Err] Unicode error in: '{file}'.\n Check for bad characters or convert file encoding to UTF-8.\n")
            sys.exit()
    
    return sherds


def parse_sherds(sherds, root):
    """ Parse sherd's name in list of sherds """

    sherds_parsed = []
    not_parsed = []
    
    # parser: see "Ceramics program Procedures.pdf"
    regex = re.compile(r'^([AJ])([0-9]{1,2})([qi\.])([0-9]{1,4})(?:(\.|-p)([0-9]{1,2}))?$', flags=re.I)
    #  groups:             0     1           2       3              4       5

    for sherd in sherds:
        
        parsed = regex.match(sherd)
        if not parsed:
            not_parsed += [sherd]
            continue
        
        g = parsed.groups()
        entry = {'entry': sherd.replace('i', '.', 1).capitalize(),
                 'entry_sort': f'{g[0].upper()}{g[1]:0>2}{g[2].lower().replace("i",".")}{g[3]:0>4}' +
                               (f'{g[4].lower()}{g[5]:0>2}' if g[5] else ''),
                 'path': root + f'MZ/A/{g[0].upper()}{g[1]:0>2}/O/' +
                         ('I' if (g[2].lower() in ['.', 'i']) else 'Q' + ('I' if g[4] and g[4] == '.' else 'P')) +
                         f'/{g[3]:0>4}' + (f'{g[5]:0>2}' if g[5] else '') + '.O'}
        
        if entry['entry_sort'] not in [entry['entry_sort'] for entry in sherds_parsed]:  # remove duplicates
            sherds_parsed.append(entry)

    return sherds_parsed, not_parsed


def parse_lexica(lexica_file):
    """ Parse lexica file for abbreviations: {code: {abbr: resolution,},} """
    
    lexica = dict()
    roster_codes = ''
    
    try:
        with open(lexica_file, 'r') as lines:
            for line in lines:
                line = line.strip()
                if not line or line.startswith('##') or line.startswith('>>'):
                    continue
                    
                if line.startswith('#'):
                    roster_codes = line[1:].split(';')  # get roster_codes
                    roster_codes = list(filter(None, map(str.strip, roster_codes)))  # remove spaces
                    continue
                if not roster_codes:
                    continue
                try:
                    abbr, resolution = line.split('\t', 2)[:2]
                except ValueError:  # ignore all lines without a tab
                    continue
                for roster_code in roster_codes:
                    if roster_code not in lexica:
                        lexica[roster_code] = dict()
                    lexica[roster_code].update({abbr.strip().lower(): resolution.strip()})
                    
    except IOError as err1:
        input("[Err]", str(err1))
        sys.exit()
        
    return lexica


def parse_mza_lexica(mza_lexica_file):
    """ Parse MZA lexica file for Phase's title: {phase: resolution,} """
    
    mza_phase = dict()
    try:
        with open(mza_lexica_file, 'r') as lines:
            for line in lines:
                line = line.strip()
                if not line or line.startswith(';'):
                    continue
                try:
                    phase, mza = line.split('\t', 1)
                    phase = phase.strip().rstrip(':').strip()
                    mza = mza.strip()
                    try:
                        phase = phase.split(' ', 1)[1].strip()
                    except ValueError:
                        pass
                    
                    mza_phase.update({phase: mza})
                    
                except ValueError:  # ignore all lines without a tab
                    pass
    
    except IOError as err1:
        input("[Err]", str(err1))
        sys.exit()
    
    return mza_phase


def read_sherd_files(sherds_parsed, lexica):
    """ Read sherds data from secondary input, found from parsed sherd's name """
    
    ceramics = []
    not_found = []
    no_shape = []
    
    for sherd in sherds_parsed:
        # clear all, calculate all, then build dict()
        feature, stratum, stratum_ss, phase, phase_ss, ware, shape, image, family, sub_family, type, details = [''] * 12
        try:
            with open(sherd['path'], 'r') as lines:
                for line in lines:
                    if line.startswith(' '):
                        continue
                    info = line.strip().split('\t')
                    info = list(map(str.strip, info))  # remove extra space

                    if info[0] == 'F02':
                        feature = 'f' + re.match(r'.*?>si f([0-9]{4}).*', line).group(1).lstrip('0')
                    elif info[0] == 'I01':
                        stratum, stratum_ss = info[3].split('-', 1)
                    elif info[0] == 'I03':
                        phase, phase_ss = info[3].split('-', 1)
                    elif info[0] == 'K03':
                        ware = info[3]
                    elif info[0] == 'K04':
                        shape = info[3]
                    elif info[0] == 'O04':
                        image = info[3]
                    elif info[0] == 'ZcaS1':
                        family = info[3]
                    elif info[0] == 'ZcaS2':
                        sub_family = info[3]
                    elif info[0] == 'ZcaS3':
                        type = info[3]
                    elif info[0] == 'ZcaS4':
                        details = info[3]
    
                feature_long = (sherd['entry_sort'][:3] + (f'f{feature[1:]:0>4}' if not feature[-1].isalpha()
                                else f'f{feature[1:-1]:0>4}' + feature[-1]))\
                    if feature else ''
                stratum_long = (f's{stratum[1:]:0>3}' if not stratum[-1].isalpha()
                                else f's{stratum[1:-1]:0>3}' + stratum[-1])\
                    if stratum else ''
                ware_long = (lexica['K3'].get(ware.lower(), ware)).title()
                overall = lexica['K4'].get(shape.lower(), shape)
                family_long = lexica['ZcaS1'].get(family.lower(), family)
                link = sherd['path'].replace('/O/', '/D/', 1)[:-2] + '.htm'
                if shape.lower() in lexica['K4']:
                    main_shape = lexica['K4'].get(shape.lower())  # .split(' ',1)[0]
                elif details.lower() in lexica['ZcaS4']:
                    main_shape = lexica['ZcaS4'].get(details.lower()).split(':', 1)[0]
                else:
                    no_shape.append(sherd['entry'])
                    continue  # NO main_shape found
                if not phase:
                    no_shape.append(sherd['entry'])
                    continue  # NO phase found (do we need a different list?)
                
                shape_code = ''.join([x or '-' for x in
                    (shape, family + '.' if family != '-' and len(family) == 1 else family, sub_family, type, details)])\
                    .rstrip("-.")
    
                ceramics.append(
                    dict(entry=sherd['entry'], entry_sort=sherd['entry_sort'], shape_code=shape_code, shape=shape,
                         family=family, sub_family=sub_family, family_long=family_long, type=type, details=details,
                         ware=ware, feature=feature, feature_long=feature_long, stratum=stratum, stratum_ss=stratum_ss,
                         stratum_long=stratum_long, phase=phase, phase_ss=phase_ss, ware_long=ware_long,
                         main_shape=main_shape, overall=overall, link=link, image=image))

                # if sherd['entry'] in ['A16.63', 'J1q1168.8', 'J2q374-p1']:  print(ceramics[-1])

        except IOError:
            not_found += [sherd['entry']]
    
    return ceramics, not_found, no_shape


def write_html(ceramics, template_index, out_index, out_index_vessel, template_strata, out_strata_dir, out_database):
    """ Generate HTML from data formatted in the templates and write to files """
    ### TODO: reformat code

    date = datetime.date.today().strftime('%B %Y')  # "Month yyyy"
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('.'))  # template loader
    
    # --- Index ---
    template = env.get_template(template_index)
    
    # list (instead of dict) for ease of use in templates
    # indices = [[index, href, type, total, sub],]
    #   sub = [(sub_type, sub_type_lex, sub_link, sort, sub_total, sherds),]
    #      sherds = [(sherd, sherd_link),]
    
    sub_ = defaultdict(lambda: [0, []])  # {(sub_type, sub_type_lex, sub_link, sort): [sub_total, [(entry, link),]]}
    
    phase = ["phase", "phase", "Phase [with link to Synopsis]", 0, sub_.copy()]
    stratum = ["stratum", "stratum", "Stratum [with link to Synopsis]", 0, sub_.copy()]
    feature = ["feature", "feature", "Feature [with link to Synopsis]", 0, sub_.copy()]
    ware = ["ware", "ware", "Ware [with link to Synopsis]", 0, sub_.copy()]
    main = ["shape: overall", "shapemain", "Shape [with link to Synopsis]", 0, sub_.copy()]
    family = ["shape: overall / family", "shapefamily", "Shape", 0, sub_.copy()]
    subfamily = ["shape: overall / family / sub-family", "shapesubfamily", "Shape", 0, sub_.copy()]
    type = ["shape: overall / family / sub-family / type", "shapetype", "Shape", 0, sub_.copy()]
    detail = ["shape: overall / family / sub-family / type / detail", "shapedetail", "Shape", 0, sub_.copy()]
    onlydetail = ["shape: details [overall not defined]", "shaperimbase", "Shape", 0, sub_.copy()]
    comprensive = ["shape: comprehensive", "shapecomprehensive", "Shape", 0, sub_.copy()]
    unit = ["unit", "unit", "Unit", 0, sub_.copy()]
    vessel_sherd = ["vessel and sherd", "sherd", "Sherd", 0, []]  # "vessel and sherd" in different file because very big
    
    indices = [phase, stratum, feature, ware, main, family, subfamily, type, detail, onlydetail, comprensive, unit]
    
    sep = ' / '

    ceramics.sort(key=lambda x: x['entry_sort'])
    for cer in ceramics:
        for cer_index in indices:
            if cer_index is phase:
                sub_type = "Phase " + cer['phase'][1:] +\
                           (" - " + mza_phase.get(cer['phase'][1:]) if cer['phase'][1:] in mza_phase else "")
                sub_type_lex = ''
                sub_link = "/MZ/A/CERAMICS/TEXTS/C2/strata/phase" + cer['phase'][1:] + ".htm"
                sort = cer['phase'][1:]
            elif cer_index is stratum:
                if not cer['stratum']: continue
                sub_type = cer['stratum']
                sub_type_lex = ''
                sub_link = "/MZ/A/CERAMICS/TEXTS/C2/strata/" + cer['stratum_long'] + ".htm"
                sort = cer['stratum_long']
            elif cer_index is feature:
                if not cer['feature']: continue
                sub_type = cer['entry_sort'][0] + cer['entry_sort'][1:3].lstrip('0') + cer['feature']
                sub_type_lex = ''
                sub_link = "/MZ/A/CERAMICS/TEXTS/C2/strata/" + cer['feature_long'] + ".htm"
                sort = cer['feature_long']
            elif cer_index is ware:
                if not cer['ware']: continue
                sub_type = cer['ware_long']
                sub_type_lex = cer['ware']
                sub_link = "/MZ/A/CERAMICS/TEXTS/C2/strata/" + cer['ware'] + ".htm"
                sort = ''
            elif cer_index is main:
                if not cer['shape']: continue
                sub_type = cer['overall']
                sub_type_lex = cer['shape']
                sub_link = "/MZ/A/CERAMICS/TEXTS/C2/strata/" + cer['overall'].replace(' ', '_') + ".htm"
                sort = ''
            elif cer_index is family:
                if not cer['family']: continue
                sub_type = cer['overall'] + sep + lexica['ZcaS1'].get(cer['family'].lower(), cer['family'])
                sub_type_lex = (cer['shape'] or '-') + cer['family']
                sub_link = "/MZ/A/CERAMICS/TEXTS/A2/shapes-codes.htm#" + sub_type_lex
                sort = ''
            elif cer_index is subfamily:
                if not cer['sub_family']: continue
                sub_type = cer['overall'] + sep + lexica['ZcaS1'].get(cer['family'].lower(), cer['family'] or '-')\
                           + sep + lexica['ZcaS2'].get(cer['sub_family'].lower(), cer['sub_family'])
                sub_type_lex = cer['shape'] + (cer['family'] + '.' if len(cer['family']) == 1 else (cer['family'] or '-')) + cer['sub_family']
                sub_link = "/MZ/A/CERAMICS/TEXTS/A2/shapes-codes.htm#" + sub_type_lex
                sort = ''
            elif cer_index is type:
                if not cer['type']: continue
                sub_type = cer['overall'] + sep + lexica['ZcaS1'].get(cer['family'].lower(), cer['family'] or '-')\
                           + sep + lexica['ZcaS2'].get(cer['sub_family'].lower(), cer['sub_family'] or '-') + sep + cer['type']
                sub_type_lex = cer['shape'] + (cer['family'] + '.' if len(cer['family']) == 1 else (cer['family'] or '-'))\
                               + (cer['sub_family'] or '-') + cer['type']
                sub_link = "/MZ/A/CERAMICS/TEXTS/A2/shapes-codes.htm#" + sub_type_lex
                sort = ''
            elif cer_index is detail:
                if not cer['shape'] or not cer['details']: continue
                sub_type = cer['overall'] + sep + lexica['ZcaS1'].get(cer['family'].lower(), cer['family'] or '-')\
                           + sep + lexica['ZcaS2'].get(cer['sub_family'].lower(), cer['sub_family'] or '-')\
                           + sep + (cer['type'] or '-') + sep + lexica['ZcaS4'].get(cer['details'].lower(), cer['details'])
                sub_type_lex = cer['shape'] + (cer['family'] + '.' if len(cer['family']) == 1 else (cer['family'] or '-'))\
                               + (cer['sub_family'] or '-') + (cer['type'] or '-') + cer['details']
                sub_link = "/MZ/A/CERAMICS/TEXTS/A2/shapes-codes.htm#" + sub_type_lex
                sort = ''
            elif cer_index is onlydetail:
                if cer['shape'] or not cer['details']: continue
                sub_type = lexica['ZcaS4'].get(cer['details'].lower(), cer['details'])
                sub_type_lex = '----' + cer['details']
                sub_link = "/MZ/A/CERAMICS/TEXTS/A2/shapes-codes.htm#" + sub_type_lex
                sort = ''
            elif cer_index is comprensive:
                sub_type = ((cer['overall'] or '-') + sep + lexica['ZcaS1'].get(cer['family'].lower(), cer['family'] or '-')
                            + sep + lexica['ZcaS2'].get(cer['sub_family'].lower(), cer['sub_family'] or '-') + sep + (cer['type'] or '-')
                            + sep + lexica['ZcaS4'].get(cer['details'].lower(), cer['details'] or '-')).strip(sep + '-')
                sub_type_lex = cer['shape_code']
                sub_link = "/MZ/A/CERAMICS/TEXTS/A2/shapes-codes.htm#" + sub_type_lex
                sort = ''
            elif cer_index is unit:
                sub_type = cer['entry_sort'][0] + cer['entry_sort'][1:3].lstrip('0')
                sub_type_lex = ''
                sub_link = "/MZ/A/" + cer['entry_sort'][:3] + "/UGR/-frame.htm"
                sort = cer['entry_sort'][:3]
            
            cer_index[4][(sub_type, sub_type_lex, sub_link, sort)][0] += 1
            cer_index[4][(sub_type, sub_type_lex, sub_link, sort)][1].append((cer['entry'], cer['link']))
    
    # make totals
    for cer_index in indices:
        total = 0
        sub_ = []
        for sub_item in sorted(cer_index[4].items(), key=lambda x: (x[0][3], x[0][0])):  # sort by 'sort' and 'sub_type'
            total += sub_item[1][0]  # add 'sub_total'
            sub_.append((sub_item[0][0], sub_item[0][1], sub_item[0][2], sub_item[0][3], sub_item[1][0], sub_item[1][1]))
            #            sub_type,       sub_type_lex,   sub_link,       sort,           sub_total,      sherds

        cer_index[3] = total
        cer_index[4] = sub_
    
    # "Index by vessel and sherd" in a separate file
    units = []  # different 'unit' for menu
    old_unit = ''
    i = -1
    for cer in ceramics:  # already sorted
        unit = cer['entry_sort'][0] + cer['entry_sort'][1:3].lstrip('0')
        if old_unit != unit:
            old_unit = unit
            i += 1
            units.append((unit, []))
    
        sherd_vs = cer['entry']
        sherd_link_vs = cer['link']
        phase_vs = cer['phase'][1:]
        phase_link_vs = "/MZ/A/CERAMICS/TEXTS/C2/strata/phase" + cer['phase'][1:] + ".htm"
        ware_vs = (lexica['K3'].get(cer['ware'].lower(), cer['ware'])).title()
        ware_link_vs = "/MZ/A/CERAMICS/TEXTS/A2/ware-" + cer['ware'] + ".htm"
        main_shape_vs = cer['main_shape']
        if cer['shape'].lower() in lexica['K4']:
            main_shape_link_vs = "/MZ/A/CERAMICS/TEXTS/A2/shapes-codes.htm#" + cer['shape']
        else:
            main_shape_link_vs = "/MZ/A/CERAMICS/TEXTS/A2/shapes-codes.htm#----" + cer['details']
    
        units[i][1].append((sherd_vs, sherd_link_vs, phase_vs, phase_link_vs, ware_vs, ware_link_vs, main_shape_vs, main_shape_link_vs))
    
    vessel_sherd[3] = indices[0][3]  # total, same as 'phase'
    vessel_sherd[4] = units
    sherds_all = (vessel_sherd,)
    
    filename_index = out_index.split('/')[-1]
    filename_index_vessel = out_index_vessel.split('/')[-1]
    temp = template.render(date=date, indices=indices, filename_index=filename_index, filename_index_vessel=filename_index_vessel, vessel_sherd=vessel_sherd[0])
    temp_vessel = template.render(date=date, sherds_all=sherds_all, filename_index=filename_index, filename_index_vessel=filename_index_vessel)
    
    try:
        with open(out_index, 'w') as html:
            html.write(temp)
        with open(out_index_vessel, 'w') as html:
            html.write(temp_vessel)

    except IOError as err1:
        print("[Err]", str(err1))
    
    
    # --- Strata ---
    # data = [[shape, sub],]
    #   sub = [(sherd,shape_code,ware,sherd0,feature,stratum,stratum_ss,link,image),]

    block_menu = dict()
    for index, href, type, total, sub_ in indices:
        if index == ware[0]:
            for sub_type, sub_type_lex, sub_link, sort, sub_total, sherds in sub_:
                lines_menu = ''
                for line in template.blocks['menu'](template.new_context(
                        {'sub_type': sub_type, 'sub_type_lex': sub_type_lex, 'sub_link': sub_link, 'sort': sort,
                         'sub_total': sub_total, 'sherds': sherds})):
                    lines_menu += line
                block_menu.update({'ware_' + sub_type: lines_menu})
        elif index == main[0]:
            for sub_type, sub_type_lex, sub_link, sort, sub_total, sherds in sub_:
                lines_menu = ''
                for line in template.blocks['menu'](template.new_context(
                        {'sub_type': sub_type, 'sub_type_lex': sub_type_lex, 'sub_link': sub_link, 'sort': sort,
                         'sub_total': sub_total, 'sherds': sherds})): lines_menu += line
                block_menu.update({'overall_' + sub_type: lines_menu})
    
    template = env.get_template(template_strata)

    shape_order = ('bowl', 'jar', 'pot', None, 'base', 'handle', 'rim', None)
    
    for strata in ('phase', 'stratum_long', 'feature_long', 'ware_long', 'overall'):
        data = []
        index = []
        new_shape = None
        new = ceramics[0][strata]
        y = 0  # for shape_order
        before = ''  # for top navigation
        after = ''  # for top navigation
        stratum = set()
        feature = set()
        group_by = 'main_shape' if not strata == 'overall' else 'family_long'
    
        ceramics.sort(key=lambda cer: (cer[strata],
            str(shape_order.index(cer[group_by])) if cer[group_by] in shape_order else (cer[group_by] if cer[group_by] else 'zzz'),
            cer['entry_sort']))  # sort by cer, shape_order/main_shape, sherd name

        for x in range(len(ceramics)):
            if ceramics[x][strata]:
    
                if ceramics[x][group_by] != new_shape:  # for new main_shape
                    new_shape = ceramics[x][group_by]
                    data.append([new_shape or 'No sub-category', []])

                    # generate index menu
                    if y < len(shape_order):
                        while shape_order[y] != new_shape:
                            if not shape_order[y] and index and index[-1]:  # empty line when 'None' in shape_order
                                index += ['']
                            y += 1
                            if y == len(shape_order):
                                break
                        y += 1
                    if not new_shape and index and index[-1]:  # empty line when empty new_shape
                        index += ['']
                    index += [new_shape or 'No sub-category']
                
                data[-1][1] += [(ceramics[x]['entry'], ceramics[x]['shape_code'], ceramics[x]['ware'],
                                 ceramics[x]['entry_sort'], ceramics[x]['feature'][1:], ceramics[x]['stratum'][1:],
                                 ceramics[x]['stratum_ss'], ceramics[x]['link'], ceramics[x]['image'])]
                
                if strata == 'phase':
                    if ceramics[x]['stratum_long']:
                        stratum.update({ceramics[x]['stratum_long']})
                    if ceramics[x]['feature_long']:
                        feature.update({ceramics[x]['feature_long']})
                
                if len(ceramics)-1 == x or ceramics[x+1][strata] != new:  # for each different cer[strata], write new file
                    if strata == 'phase':
                        filename = 'phase' + new[1:] + '.htm'
                        title = new
                        # update menu for phase,stratum,feature
                        lines_menu = ''
                        for line in template.blocks['menu'](template.new_context({'phase': ceramics[x]['phase'][1:],
                                                  'stratum': sorted(list(stratum)), 'feature': sorted(list(feature))})):
                            lines_menu += line
                        block_menu.update({ceramics[x]['phase']: lines_menu})
                        menu = block_menu[ceramics[x]['phase']]
                    elif strata == 'stratum_long':
                        filename = new + '.htm'
                        title = 's' + new[1:].lstrip('0')
                        menu = block_menu[ceramics[x]['phase']]
                    elif strata == 'feature_long':
                        filename = new + '.htm'
                        title = new[0] + new[1:3].lstrip('0') + 'f' + new[4:].lstrip('0')
                        menu = block_menu[ceramics[x]['phase']]
                    elif strata == 'ware_long':
                        filename = ceramics[x]['ware'] + '.htm'
                        title = ceramics[x]['ware']
                        menu = block_menu['ware_' + ceramics[x][strata]]
                    elif strata == 'overall':
                        filename = ceramics[x]['overall'].replace(' ', '_') + '.htm'
                        title = ceramics[x]['overall']
                        menu = block_menu['overall_' + ceramics[x][strata]]
                    else:
                        break
    
                    if not len(ceramics)-1 == x:
                        after = ceramics[x+1][strata]
                    else:
                        after = ''
                    
                    temp = template.render(index=index, data=data, title=title, after=after[1:], before=before[1:],
                                           phase=ceramics[x]['phase'][1:], strata=strata, date=date, menu=menu)
                    
                    try:
                        with open(out_strata_dir + filename, 'w') as html:
                            html.write(temp)
                    except IOError as err1:
                        print("[Err]", str(err1))
    
                    before = new
                    new = after
                    new_shape = None
                    data = []
                    index = []
                    y = 0
                    stratum = set()
                    feature = set()
            else:
                new = ceramics[x+1][strata]
    
    
    # --- Database ---
    top_row = ('vessel/sherd', 'shape code', 'main shape (K04)', 'family (ZcaS1)', 'sub-family (ZcaS2)', 'type (ZcaS3)',
               'details (ZcaS4)', 'ware (K03)', 'feature (F02)', 'stratum (I01)', 'phase (I03)', 'image (O04)')
    
    data = []
    ceramics.sort(key=lambda cer: cer['entry_sort'])
    for cer in ceramics:
        data.append((cer['entry_sort'], cer['shape_code'], cer['shape'], cer['family'], cer['sub_family'], cer['type'],
                    cer['details'], cer['ware'], cer['feature'], cer['stratum'], cer['phase'], cer['image']))

    try:
        with open(out_database, 'w') as db:
            db.write('\t'.join(top_row) + '\n')
            for d in data:
                db.write('\t'.join(d) + '\n')
    
    except IOError as err1:
        print("[Err]", str(err1))
    
    return


def write_errors(sherds_dir, not_parsed, not_parsed_file, not_found, not_found_file, no_shape, no_shape_file):
    """ Write list of errors found by the program """
    
    if not_parsed:
        print(f"[Err] Some Sherds not parsed. List written to: '{not_parsed_file}'")
        try:
            with open(not_parsed_file, 'w') as text:
                text.write(f"Primary input in '{sherds_dir}' not parsed for following sherds.\n\n" +
                           "\n".join(not_parsed) + "\n")
        except IOError as err1:
            print("[Err]", str(err1))

    if not_found:
        print(f"[Err] Some Inputs not found. List written to: '{not_found_file}'")
        try:
            with open(not_found_file, 'w') as text:
                text.write("Secondary input not found for following sherds.\n\n" + "\n".join(not_found) + "\n")
        except IOError as err1:
            print("[Err]", str(err1))

    if no_shape:
        print(f"[Err] Some Shapes not found. List written to: '{no_shape_file}'")
        try:
            with open(no_shape_file, 'w') as text:
                text.write("Shape or phase not found for following sherds.\n\n" + "\n".join(no_shape) + "\n")
        except IOError as err1:
            print("[Err]", str(err1))

    return


# PROGRAM MAIN
if __name__ == '__main__':

    # cd to program directory for relative links
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    os.chdir(__location__)

    # Save console text to LOG
    logger = Logger()
    sys.stdout = logger
    sys.stderr = logger
    
    # start
    print(f'''
 CerPhaS
-----------------------------------------------

 Ceramics Digital Book - Shapes by phase/stratum

 Primary input path: '{SHERDS_DIR}'
 Lexica: '{LEXICA_FILE}'
 Output: '{OUT_STRATA_DIR}', '{OUT_INDEX}', '{OUT_DATABASE}'
''')

    try:
        input('Press ENTER to Continue, Ctrl-C to Abort.\n')
    except KeyboardInterrupt:  # exit with Ctrl-C
        sys.exit()

    print('\n[*] Reading files...')
    sherds = read_all_files(SHERDS_DIR)
    sherds_parsed, not_parsed = parse_sherds(sherds, ROOT)
    lexica = parse_lexica(LEXICA_FILE)
    mza_phase = parse_mza_lexica(MZA_LEXICA_FILE)

    print('\n[*] Processing input & generating HTML...')
    ceramics, not_found, no_shape = read_sherd_files(sherds_parsed, lexica)

    print('\n[*] Writing data...')
    write_html(ceramics, TEMPLATE_INDEX, OUT_INDEX, OUT_INDEX_VESSEL, TEMPLATE_STRATA, OUT_STRATA_DIR, OUT_DATABASE)
    write_errors(SHERDS_DIR, not_parsed, NOT_PARSED_FILE, not_found, NOT_FOUND_FILE, no_shape, NO_SHAPE_FILE)

    print('\n[+] Done!')

    input()
    sys.exit()
