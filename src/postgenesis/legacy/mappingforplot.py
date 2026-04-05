#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 31 22:12:31 2025

@author: duoxup
"""

from usrparas import umap
from .dictx import CaseInsensitiveDict as dictX
import interface as xki
import copy

mapping_dict = copy.deepcopy(umap)

stat_data_mapping = dictX(
    max_power = dictX(),
    max_energy = dictX(),
    max_ppower = dictX(),
    peak_frequency = dictX(),
    sigma_t = dictX(),
    z = dictX(),
    energy = dictX(),
    )

smap = stat_data_mapping
for key, value in smap.items():
    value.update(unit=None)



bd = xki.BeamDiagnostics()
for key, unit in bd.keyUnit.items():
    temp_dict = {key: dictX(unit=unit)}
    if key not in umap:
        smap.update(**temp_dict)



for key, value in smap.items():
    value.update(plot_label=key,
                 title_label=key,
                 )

smap['max_power'].update(unit='W', plot_label = 'Max. total power') #Maximal iunstantaneous total radiation power (integrate along z)
smap['max_energy'].update(unit='J', plot_label = 'Pluse energy', title_label = 'Pluse energy') 
smap['max_ppower'].update(unit='W', plot_label = 'Max. peak power') #Maximal iunstantaneous peak radiation power (maximum along z)
smap['peak_frequency'].update(unit='Hz', plot_label = 'Peak radiation frequency')
smap['sigma_t'].update(unit='s', plot_label = r'$\sigma_t$', title_label='Pulse length')
smap['std_z'].update(unit='mm', plot_label = r'$\sigma_z$', title_label='Bunch length')
smap['z'].update(unit='m', plot_label = 'z', title_label='z')
smap['energy'].update(unit='J', plot_label = 'Pluse energy', title_label = 'Pluse energy') 


mapping_dict.update(**smap)





mdp = mapping_dict