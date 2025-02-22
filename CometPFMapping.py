#!/usr/bin/env python
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Sun Dec 13, 2020 at 11:30 PM +0100

from pathlib import Path

from pyUTM.io import write_to_csv

from UT_Aux_mapping.const import output_dir
from UT_Aux_mapping.helpers import filter_comp, make_comp_comp_dict

from CometDcbMapping import path_finder_descr, \
    comet_j1_j2_duo_to_fpga, filter_path_finder_throw_gnd

comet_pf_mapping_filename = output_dir / Path('CometPFMapping.csv')


#############
# Filtering #
#############

# We care about JN (U.FL connectors) to COMET
path_finder_result = filter_comp(path_finder_descr, r'^COMET|^J\d+$')
path_finder_result = list(filter(filter_path_finder_throw_gnd,
                                 path_finder_result))


#################################################################
# Find Pathfinder connections between COMET connectors and JD10 #
#################################################################

path_finder_connections_raw = [
    make_comp_comp_dict(path_finder_result, j, c)
    for c in ['COMET_A_J1', 'COMET_A_J2', 'COMET_B_J1', 'COMET_B_J2']
    for j in ['J'+str(k) for k in range(1, 38)]
]

# Again, combine into a single dictionary.
path_finder_ufl_to_comet = {k: v for d in path_finder_connections_raw
                            for k, v in d.items()}


####################
# Make connections #
####################

# Pathfinder -> COMET -> COMET DB -> COMET #####################################

comet_ufl_data = []

for ufl_pin, comet_pin in path_finder_ufl_to_comet.items():
    row = []

    fpga_pin = comet_j1_j2_duo_to_fpga[comet_pin]
    row.append('-'.join(fpga_pin))

    row.append('-'.join(comet_pin))
    row.append('-'.join(ufl_pin))

    comet_ufl_data.append(row)

comet_ufl_data.sort(key=lambda x: int(x[2].split('-')[0][1:]))


#################
# Output to csv #
#################

# COMET FPGA -> Pathfinder U.FL, full ##########################################

write_to_csv(
    comet_pf_mapping_filename, comet_ufl_data,
    ['COMET FPGA pin', 'Pathfinder COMET connector',
     'Pathfinder U.FL connector']
)
