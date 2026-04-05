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

cluster_folder = r'/lustre/fs25/group/pitz/duoxup/THzSuperRad/genesis/cluster00000201/'
fname =  '001.g4.000.out.h5.csv'

dfb = pd.read_csv(os.path.join(cluster_folder,fname))
df = dfb.copy()
df['index'] = df.index

# dfc = df[df['sig_x']<0.4]
# dfc = df[df['Q_total']==-1000]
# dfc = df[df['cor_Ekin']==0]
dfc = df
dfc['Q_total'] = np.abs(df['Q_total'])
meta_plot = ColumnMetaRegistry.from_json(r'/afs/ifh.de/group/pitz/data/duoxup/sim1/pyS/colmeta_4.json')
psc = PlotScanConfig(ncols=5, meta=meta_plot,
                     sharex='col',
                     # sharey='row',
                     # sharex=False,
                     sharey=False,
                     )

fig, axes = plot_scan_facets(df=dfc,
                             x='I_peak',
                             # y='max_energy',
                             # y='fwhm@80%_max_energy',
                             y='fwhm@0.39m',
                             # y='energy@0.39m',
                             # y='sigma_t@80%_max_energy',
                             # y='sigma_t@0.11m',  # 'max_energy'  'sigma_t@90%_max_energy'
                             hue='beta_x_scale_from_opt',
                             # hue='sig_x',
                             facet_vars=['Q_total', 'Freq'],
                             config=psc,
                             mode='line',
                             colorbar='each',
                             cmap='viridis',
                             no_autoscale=['Q_total', 'cor_Ekin', 'sig_z', 'sig_x', 'Freq'])
for ax in axes.flatten():
    ax.grid(True)
fig.suptitle(wrap_text(cluster_folder, 100))
xtils.save_figure_auto_date(fig)