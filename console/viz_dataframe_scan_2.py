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
cluster_folder = r'/lustre/fs25/group/pitz/duoxup/THz_ideal_machine/genesis/cluster00000008/'
fname =  '001.g4.000.out.h5.csv'

dfb = pd.read_csv(os.path.join(cluster_folder,fname))
df = dfb.copy()
# df['index'] = df.index
for q in [-3000]:
    # dfc = df[df['sig_x']<0.4]
    # dfc = df[df['oth_lambda0_um']== 300]
    # dfc = df[(df['oth_lambda0_um']== 300) & (df['oth_q'] == q)]
    # dfc = df[(df['oth_lambda0_um']== 300) & (df['oth_beta_x0'] == 1)]
    dfc = df[(df['oth_q']== q)]
    # dfc = dfc[dfc['oth_lambda0_um']==300]
    # dfc = df[df['cor_Ekin']==0]
    # dfc = df
    
    # dfc['oth_q'] = np.abs(df['oth_q'])
    # cols = dfc.columns.tolist()
    # i = cols.index('oth_q')
    # j = cols.index('gen_input_cor_ekin')
    # cols[i], cols[j] = cols[j], cols[i]
    # dfc = dfc[cols]
    
    # dfc = dfc[dfc['oth_beta_x0'].isin(dfc['oth_beta_x0'].unique()[::2])]
    
    
    
    
    
    
    
    
    
    
    #%% Main
    
    meta_plot = ColumnMetaRegistry.from_json(r'/afs/ifh.de/group/pitz/data/duoxup/sim1/pyS/colmeta_5.json')
    psc = PlotScanConfig(ncols=6, meta=meta_plot,
                         figsize_per_ax=[3, 4],
                         sharex='col',
                         sharey='all',
                         # sharex=False,
                         # sharey=False,
                         )
    
    zt = 0.65
    at_max = '80%'
    fig, axes = plot_scan_facets(df=dfc,
                                 x='oth_beta_x0',
                                 # y='max_energy',
                                 # y='fwhm@80%_max_energy',
                                 # y=f'sigma_t@{zt}m',
                                 # y = 'max_ppower',
                                 # y=f'energy@{zt}m',
                                 y=f'sigma_t@{at_max}_max_energy',
                                 # y='sigma_t@0.11m',  # 'max_energy'  'sigma_t@90%_max_energy'
                                 hue='oth_i_peak',
                                 # hue='sig_x',
                                 facet_vars=['oth_q','gen_input_cor_ekin'],
                                 config=psc,
                                 mode='heatmap',
                                 colorbar='row',
                                 cmap='gist_heat',
                                 no_autoscale=['oth_q', 'oth_beta_x0', 'oth_width_mb', 'oth_lambda0_um'])
    # for ax in axes.flatten():
    #     ax.grid(True)
    fig.suptitle(wrap_text(cluster_folder, 100))
    xtils.save_figure_auto_date(fig)