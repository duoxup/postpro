#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 17:07:08 2026

@author: duoxup
"""

import os
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import xtils

from postgenesis.vizdfscan import PlotScanConfig, ColumnMetaRegistry, plot_scan_facets
from postgenesis.utils.text import wrap_text
from cycler import cycler

mpl.rcdefaults()
mpl.rcParams['axes.prop_cycle'] = cycler(color=plt.get_cmap('tab10').colors) * cycler(linestyle=['-','--','-.',':'])

figsize_base = (6, 4)
plt.rcParams['figure.figsize'] = figsize_base


#%% Load data and preprocess
cluster_folder = r'/lustre/fs25/group/pitz/duoxup/THz_ideal_machine/genesis/cluster00000002/'
fname =  '001.g4.000.out.h5.csv'

dfb = pd.read_csv(os.path.join(cluster_folder,fname))
df = dfb.copy()
# df['index'] = df.index

# dfc = df[df['sig_x']<0.4]
dfc = df[df['oth_lambda0_um']== 300]
# dfc = df[df['cor_Ekin']==0]
# dfc = df
dfc['oth_q'] = np.abs(df['oth_q'])










#%% Main

meta_plot = ColumnMetaRegistry.from_json(r'/afs/ifh.de/group/pitz/data/duoxup/sim1/pyS/colmeta_4.json')
psc = PlotScanConfig(ncols=4, meta=meta_plot,
                     sharex='col',
                     sharey='col',
                     # sharex=False,
                     # sharey=False,
                     )

fig, axes = plot_scan_facets(df=dfc,
                             x='oth_width_mb',
                             # y='max_energy',
                             # y='fwhm@80%_max_energy',
                             y='fwhm@0.65m',
                             # y = 'max_ppower',
                             # y='energy@0.65m',
                             # y='sigma_t@80%_max_energy',
                             # y='sigma_t@0.11m',  # 'max_energy'  'sigma_t@90%_max_energy'
                             hue='oth_beta_x0',
                             # hue='sig_x',
                             facet_vars=['oth_q', 'scr_pslc_cor_pz'],
                             config=psc,
                             mode='line',
                             colorbar='each',
                             cmap='viridis',
                             no_autoscale=['oth_q', 'oth_beta_x0', 'oth_width_mb', 'oth_lambda0_um'])
for ax in axes.flatten():
    ax.grid(True)
fig.suptitle(wrap_text(cluster_folder, 100))
xtils.save_figure_auto_date(fig)