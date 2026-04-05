#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 22:18:09 2026

@author: duoxup
"""

from postgenesis.vizdfscan import ColumnMeta, ColumnMetaRegistry, make_registry

old_gcmr = ColumnMetaRegistry.from_json('../src/postgenesis/gcmr_1.json')
old_dict = old_gcmr.to_dict()['metas']

new_dict = {}
for k in old_dict:
    if ('phi' in k) | ('phase' in k):
        v = {"unit": "rad", "axis_label": "Phase", "scale": 1, "digits_show": 3}
    elif ('intfar' in k) | ('intnear' in k):
        v = {"unit": "a.u.", "axis_label": "Intensity", "scale": 1, "digits_show": 2}
    elif k=='g_s':
        v = {"unit": "m", "axis_label": "s", "scale": 1, "digits_show": 2}
    elif k=='zsigmat_fld':
        v = {"unit": "s", "axis_label": "$\\sigma_t$", "scale": 1, "digits_show": 2}
    elif k=='current':
        v = {"unit": "A", "axis_label": "Current", "scale": 1, "digits_show": 2}
    elif (k=='zenergy') | (k=='fld_g_energy'):
        v = {"unit": "J", "axis_label": "Pulse energy", "scale": 1, "digits_show": 2}
    elif k=='t_from_s':
        v = {"unit": "s", "axis_label": "Time", "scale": 1, "digits_show": 2}
    elif 'lambda' in k:
        v = {"unit": "m", "axis_label": "Wavelength", "scale": 1, "digits_show": 2}
    elif 'beta' in k:
        v = {"unit": "m", "axis_label": "$\\beta$", "scale": 1, "digits_show": 2}
    elif 'divergence' in k:
        v = {"unit": "rad", "axis_label": "Divergence", "scale": 1, "digits_show": 3}
    elif ('size' in k) and ('mpi' not in k):
        v = {"unit": "m", "axis_label": "Size", "scale": 1, "digits_show": 2}
    elif 'pointing' in k:
         v = {"unit": "a.u.", "axis_label": "Pointing Vector", "scale": 1, "digits_show": 2}
    elif k == 'power':
         v = {"unit": "W", "axis_label": "Power", "scale": 1, "digits_show": 2}
    elif 'position' in k:
         v = {"unit": "m", "axis_label": "Position", "scale": 1, "digits_show": 2}
    elif 'frequency' in k:
         v = {"unit": "Hz", "axis_label": "Frequency", "scale": 1, "digits_show": 2}   
    elif ('pxmin' in k) | ('pxmax' in k) | ('pymin' in k) | ('pymax' in k):
         v = {"unit": "", "axis_label": "Momentum", "scale": 1, "digits_show": 2}   
    elif ('xmin' in k) | ('xmax' in k) | ('ymin' in k) | ('ymax' in k):
         v = {"unit": "m", "axis_label": "Position", "scale": 1, "digits_show": 2}   
    elif k.startswith('d'):
         v = {"unit": "m", "axis_label": "Difference", "scale": 1, "digits_show": 2}   
    else:
        v = {"unit": "", "axis_label": k, "scale": 1, "digits_show": 2}
    new_dict.update({k: v})
    
new_dict.update(slice_num={"unit": "", "axis_label": 'Slice #', "scale": 1, "digits_show": 2})
new_dict.update(wavelength_spectra_int={"unit": "a.u.", "axis_label": 'Intensity', "scale": 1, "digits_show": 2})
new_dict.update(wavelength_spectra_wl={"unit": "m", "axis_label": 'Wavelength', "scale": 1, "digits_show": 2})
new_dict.update(zplot={"unit": "m", "axis_label": 'z', "scale": 1, "digits_show": 2})
new_dict.update(peakpower={"unit": "W", "axis_label": 'Peak Power', "scale": 1, "digits_show": 2})
    
gcmr = make_registry(new_dict)

gcmr.to_json('../src/postgenesis/gcmr_2.json')