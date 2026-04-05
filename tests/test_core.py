#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 22:53:47 2026

@author: duoxup
"""

from postgenesis.core import MainResults

fname = r'/lustre/fs25/group/pitz/duoxup/THzSuperRad/debug/Q=-150pC-beta_x_scale_from_opt=1.000/g4.000.out.h5'

gmr = MainResults(fname)

tmp = gmr.wavelength_spectra_wl