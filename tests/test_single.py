#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 17:14:47 2026

@author: duoxup
"""

import numpy as np
import xtils

import matplotlib.pyplot as plt
from postgenesis.singlecase import zoverview, zevo_stack, stat_one, fast_dump
from postgenesis.utils.mpl import focus_xlim_on_y_threshold

fname = r'/lustre/fs25/group/pitz/duoxup/THzSuperRad/genesis/cluster00000179/Q=-200pC-I_peak=400.000-cor_E0=0.00keV-beta_x_scale_from_opt=5.282/g4.000.out.h5'
# fname = r'/lustre/fs25/group/pitz/duoxup/THzSuperRad/genesis/cluster00000178/Q=-1000pC-I_peak=300.000-cor_E0=0.00keV-beta_x_scale_from_opt=20.000/g4.000.out.h5'
fname = r'/lustre/fs25/group/pitz/duoxup/THzSuperRad/genesis/cluster00000198/Q=-100pC-I_peak=300.000-beta_x_scale_from_opt=1.000/g4.000.out.h5'

# fig, ax = plt.subplots(figsize=[6, 3])
fig, ax = zevo_stack(fname, steps=np.arange(2, 15, 2), xattr='t_from_s')
focus_xlim_on_y_threshold(ax, threshold_abs=1e1, set_xlim=True)
# xtils.save_figure_auto_date(fig)

fig2, ax2 = zoverview(fname)
# xtils.save_figure_auto_date(fig2)
# stat_res = stat_one(fname, zs=[0.55, 1.1])
# fast_dump(fname, nsteps=3, backend='agg')