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


#%% Temporary helper
def peak_current_inverted_parabola_rel(total_charge_C: float,
                                       sigma_z_m: float,
                                       beta: float = 1.0) -> float:
    """
    Compute the peak current of a relativistic electron bunch with an
    inverted-parabola longitudinal distribution.

    Distribution:
        f(z) = 3/(4*z_max) * (1 - z^2/z_max^2),   |z| <= z_max

    with RMS bunch length:
        sigma_z = z_max / sqrt(5)

    Therefore:
        I_peak = 3 * Q * beta * c / (4 * sqrt(5) * sigma_z)

    Parameters
    ----------
    total_charge_C : float
        Total bunch charge in Coulombs.
        The sign is preserved in the returned current.
    sigma_z_m : float
        RMS bunch length in meters.
    beta : float, optional
        v / c of the bunch. Default is 1.0.

    Returns
    -------
    float
        Peak current in Amperes.
    """
    c = 299_792_458.0  # m/s

    if np.any(sigma_z_m) <= 0:
        raise ValueError("sigma_z_m must be positive.")

    I_peak = 3.0 * total_charge_C * beta * c / (4.0 * np.sqrt(5.0) * sigma_z_m)
    return I_peak


def rms_bunch_length_from_Q_I_inverted_parabola(total_charge_C: float,
                                                peak_current_A: float,
                                                beta: float = 1.0) -> float:
    """
    Compute the RMS bunch length of a relativistic electron bunch with an
    inverted-parabola longitudinal distribution from total charge and peak current.

    Distribution:
        f(z) = 3/(4*z_max) * (1 - z^2/z_max^2),   |z| <= z_max

    with:
        sigma_z = z_max / sqrt(5)

    Therefore:
        sigma_z = 3 * |Q| * beta * c / (4 * sqrt(5) * |I_peak|)

    Parameters
    ----------
    total_charge_C : float
        Total bunch charge in Coulombs.
    peak_current_A : float
        Peak current in Amperes.
    beta : float, optional
        v / c of the bunch. Default is 1.0.

    Returns
    -------
    float
        RMS bunch length sigma_z in meters.
    """
    c = 299_792_458.0  # m/s

    Q_abs = abs(total_charge_C)
    I_abs = abs(peak_current_A)

    if np.any(I_abs) <= 0:
        raise ValueError("peak_current_A must be non-zero.")

    sigma_z = 3.0 * Q_abs * beta * c / (4.0 * np.sqrt(5.0) * I_abs)
    return sigma_z

#%% Load data and preprocess
cluster_folder = r'/lustre/fs25/group/pitz/duoxup/THz_ideal_machine/genesis/cluster00000001/'
fname =  '001.g4.000.out.h5.csv'

dfb = pd.read_csv(os.path.join(cluster_folder,fname))
df = dfb.copy()
# df['index'] = df.index

# dfc = df[df['sig_x']<0.4]
dfc = df[(df['oth_lambda0_um']== 1000) & (df['oth_q']==-1100)]
# dfc = df[(df['oth_lambda0_um']== 300)]

# dfc = df[df['oth_q']==-1000]
# dfc = df
dfc['oth_q'] = np.abs(dfc['oth_q'])

# dfc['I_peak'] = peak_current_inverted_parabola_rel(dfc['oth_q']*1e-12, dfc['gen_input_sig_z']*1e-3)



# df_sl = dfc[['oth_q', 'gen_input_sig_z', 'I_peak']]





#%% Main

meta_plot = ColumnMetaRegistry.from_json(r'/afs/ifh.de/group/pitz/data/duoxup/sim1/pyS/colmeta_5.json')
psc = PlotScanConfig(ncols=6, meta=meta_plot,
                     figsize_per_ax=[3, 4],
                     sharex='col',
                     sharey='row',
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
                             # facet_vars=[ 'oth_q', 'gen_input_cor_ekin'],
                             config=psc,
                             mode='line',   #line or heatmap
                             colorbar='all',
                             cmap='viridis',
                             no_autoscale=['oth_q', 'oth_beta_x0', 'oth_width_mb', 'oth_lambda0_um'])
for ax in axes.flatten():
    ax.grid(True)
fig.suptitle(wrap_text(cluster_folder, 100))
xtils.save_figure_auto_date(fig)