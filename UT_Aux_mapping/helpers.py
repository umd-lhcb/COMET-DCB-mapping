#!/usr/bin/env python
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Tue Dec 15, 2020 at 01:01 AM +0100

import re

from collections import defaultdict
from os.path import basename
from dataclasses import dataclass
from typing import Optional


# Generate default output filename #############################################

def gen_filename(raw, addon='', ext='csv'):
    return basename(raw).split('.')[0] + addon + '.' + ext


# Regularize input #############################################################

def split_rn(descr, regexp=r'^RN\d+_\d$'):
    rn_split_dict = {
        '1': 'A',
        '8': 'A',
        '2': 'B',
        '7': 'B',
        '3': 'C',
        '6': 'C',
        '4': 'D',
        '5': 'D'
    }
    result = defaultdict(list)

    for net, comps in descr.items():
        for c in comps:
            if bool(re.search(regexp, c[0])):
                new_c = list(c)
                new_c[0] += rn_split_dict[c[1]]
                result[net].append(tuple(new_c))

            else:
                result[net].append(c)

    return dict(result)


# Filtering ####################################################################

def filter_comp(descr, regexp=r'^J\d+|^IC3_1+', netname=None):
    filtered = []

    for net, comps in descr.items():
        if netname is not None and netname not in net:
            # We also optionally filter by netname.
            pass

        else:
            processed_comps = [x for x in comps if bool(re.match(regexp, x[0]))]

            # Can't figure out any relationship if a list contains only a single
            # item.
            # We also do deduplication here.
            # Also make sure there's at least a connector component.
            if len(processed_comps) > 1 and processed_comps not in filtered \
                    and True in map(lambda x: x[0].startswith('J'),
                                    processed_comps):
                filtered.append(processed_comps)

    return filtered


def post_filter_exist(functor):
    def filter_functor(lst):
        return True if True in map(functor, lst) else False

    return filter_functor


def post_filter_any(functor):
    def filter_functor(lst):
        return False if False in map(functor, lst) else True

    return filter_functor


# Make dictionaries to find connectivity between components  ###################

def make_comp_netname_dict(descr):
    result = {}

    for net, comps in descr.items():
        for c in comps:
            result[c] = net

    return result


def make_comp_comp_dict(nested, key_comp, value_comp, strip_kw='_1'):
    result = {}

    for comps in nested:
        key_candidates = list(filter(lambda x: x[0] == key_comp, comps))
        value_candidates = list(filter(lambda x: x[0] == value_comp, comps))

        if key_candidates and value_candidates:
            if len(key_candidates) > 1 or len(value_candidates) > 1:
                raise ValueError(
                    'Unable to construct a bijection for key: {}, value: {}'.format(
                        key_candidates, value_candidates
                    ))
            else:
                # We want to strip out the '_1' part
                key = list(key_candidates[0])
                value = list(value_candidates[0])

                key[0] = key[0].replace(strip_kw, '')
                value[0] = value[0].replace(strip_kw, '')

                result[tuple(key)] = tuple(value)

    return result


def make_comp_comp_dict_bidirectional(nested):
    # NOTE: Here 'nested' should be a nx2 tensor
    result = {}

    for key1, key2 in nested:
        result[key1] = key2
        result[key2] = key1

    return result


# General netname parser #######################################################

@dataclass
class NameJP:
    jp: Optional[str] = None
    pwr: Optional[str] = None
    hyb: Optional[str] = None
    descr: str = 'GND'


def parse_net_jp(name):
    if len(fields := name.split('_')) < 2:
        return NameJP()

    jp = fields.pop(0)
    pwr = fields.pop(0)

    sep = 2 if ('EAST' in fields[1] or 'WEST' in fields[1]) else 1
    hyb = '_'.join(fields[:sep])
    descr = '_'.join(fields[sep:])

    return NameJP(jp, pwr, hyb, descr)


# PPP netname stuff ############################################################

def ppp_replacement_wrapper(rules):
    def wrapper(name):
        return rules[name] if name in rules else name
    return wrapper


def ppp_netname_regulator(
    name,
    replacement_rules=ppp_replacement_wrapper({
        # Different conventions
        'P1E': 'P1_EAST',
        'P1W': 'P1_WEST',
        'P2E': 'P2_EAST',
        'P2W': 'P2_WEST',
    }),
    typo_rules=ppp_replacement_wrapper({
        'JUP2': 'JPU2'
    })
):
    # Some of the netnames has ' ', some don't
    name = name.replace(' ', '_')

    # Now fix various inconsistencies in PPP netnames
    # So that new names agree with conventions in P2B2
    fields = [typo_rules(replacement_rules(f)) for f in name.split('_')]

    # Also need to upper case everything
    return ('_'.join(fields)).upper()


def ppp_label(
    name,
    hyb_rules=ppp_replacement_wrapper({
        'P1_EAST': 'P1E',
        'P1_WEST': 'P1W',
        'P2_EAST': 'P2E',
        'P2_WEST': 'P2W',
    }),
    lv_rules=ppp_replacement_wrapper({
        'LV_SOURCE': 'LV_SRC',
        'LV_RETURN': 'LV_RET'
    })
):
    parsed = parse_net_jp(name)
    return '_'.join([parsed.jp, hyb_rules(parsed.hyb), lv_rules(parsed.descr)])


# PPP list sorting #############################################################

def ppp_sort(name, magic=100):
    connector, pin = name.split(' - ')
    connector = int(connector[3:])
    pin = int(pin)
    return 1000 + connector*magic + pin
