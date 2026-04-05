#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 17:04:00 2026

@author: duoxup
"""

import os
import xtils
from xtils.plt import PlotCtrl
# import matplotlib.pyplot as plt
import numpy as np
import scipy

from typing import Sequence
from dstrux import Intensity1D
from importlib import resources

from .core import MainResults
from .utils.text import wrap_text
from .numerics.c1d import maximum_from_left
from .vizdfscan import ColumnMetaRegistry
from .utils.mpl import use_backend, focus_xlim_on_y_threshold

prj_dir = resources.files('postgenesis')
g_c = scipy.constants.speed_of_light
colmr = ColumnMetaRegistry.from_json(os.path.join(prj_dir, 'gcmr_2.json'))

def zoverview(fname):
    gmr = MainResults(fname)
    npics = 5
    fig, axes = xtils.new_subplots(n_subplots=npics,
                                   mode='vertical',
                                   base_size=(6, 1.8),
                                   sharex='all',
                                   layout='constrained')
    
    axes = np.asarray([axes])
    axes = axes.flatten()

    axes[0].plot(gmr.zplot, gmr.zfwhm_fld*1e12, label='FWHM') #[ps]
    axes[0].plot(gmr.zplot, gmr.zsigmat_fld*1e12, label='$\\sigma_t$') #[ps]
    # axes[0].set_ylabel('$FWHM_{t, field}$ [ps]')
    axes[0].set_ylabel('$Pulse length$ [ps]')
    axes[0].legend()

    axes[1].plot(gmr.zplot, gmr.zenergy*1e6) #[uJ]
    # axes[1].set_yscale('log')
    axes[1].set_ylabel('Pluse energy [$\\mu$J]')
    ax1t = axes[1].twinx()
    ax1t.plot(gmr.zplot, gmr.zenergy*1e6, '--') #[uJ]
    ax1t.set_yscale('log')

    axes[2].plot(gmr.zplot, gmr.par_g_xsize*1e3) #[mm]
    axes[2].plot(gmr.zplot, gmr.par_g_ysize*1e3) #[mm]
    axes[2].set_ylabel('$\\sigma_{x, part.}$ or $\\sigma_{y, part.}$ [mm]')
    axes[2].legend(['x', 'y'])

    axes[3].plot(gmr.zplot, gmr.fld_g_xsize*1e3) #[mm]
    axes[3].plot(gmr.zplot, gmr.fld_g_ysize*1e3) #[mm]
    axes[3].set_ylabel('$\\sigma_{x, field}$ or $\\sigma_{y, field}$ [mm]')
    axes[3].legend(['x', 'y'])

    axes[4].plot(gmr.zplot, gmr.fld_g_xdivergence)
    axes[4].plot(gmr.zplot, gmr.fld_g_xdivergence)
    axes[4].set_ylabel('Field divergence [rad]')
    axes[4].legend(['x', 'y'])

    axes[-1].set_xlabel('z [m]')

    for ax in axes:
        ax.grid(True)

    fig.suptitle(wrap_text(gmr.cwd, 70), fontsize=10)
    return fig, axes

def zevo_stat(fname, yattr='zenergy', fig=None, ax=None, **pltkwargs):
    gmr = MainResults(fname)
    xattr = 'zplot'
    x_colmeta = colmr.get(xattr)
    x = getattr(gmr, xattr)
    xlb = x_colmeta.axis_label
    xunt = x_colmeta.unit if x_colmeta.unit else ''       
            
    y_colmeta = colmr.get(yattr)
    y = getattr(gmr, yattr)
    ylb = y_colmeta.axis_label
    yunt = y_colmeta.unit if y_colmeta.unit else ''
    
    if (xunt != 'a.u.') and (xunt != ''):
        x_scale, x_unit_prefix = xtils.get_autoscale(x.flatten())
    else:
        x_scale, x_unit_prefix = 1, ''
    if (yunt != 'a.u.') and (yunt != ''):
        y_scale, y_unit_prefix = xtils.get_autoscale(y.flatten())
    else:
        y_scale, y_unit_prefix = 1, ''
    
    fig, ax = xtils.ensure_fig_ax(fig, ax)
    pctrl = PlotCtrl(
        x_scale=x_scale,
        x_label=xlb,
        x_unit = x_unit_prefix+xunt,
        
        y_scale=y_scale,
        y_label=ylb,
        y_unit = y_unit_prefix+yunt,
        
        data_label=None,
        unit_brk='[]',
        )
    xtils.plt.plot(x, y, pc=pctrl, fig=fig, ax=ax, **pltkwargs)
    return fig, ax
    
def zevo_stack(fname, steps: Sequence[int], xattr='t_from_s', yattr:str='intfar', fig=None, ax=None):
    gmr = MainResults(fname)
    fig, ax = xtils.ensure_fig_ax(fig, ax)
    for step in steps:
        fig, ax = zevo_line(gmr, step, xattr, yattr, fig, ax)
        ax.legend()
        fig.suptitle(wrap_text(gmr.cwd, 70), fontsize=10)
    return fig, ax


def zevo_line(gmr, step: int, xattr='t_from_s', yattr:str='intfar', fig=None, ax=None, allow_const_y=False, **pltkwargs):
    x_colmeta = colmr.get(xattr)
    x = getattr(gmr, xattr)
    xlb = x_colmeta.axis_label
    xunt = x_colmeta.unit if x_colmeta.unit else ''       
            
    y_colmeta = colmr.get(yattr)
    y = getattr(gmr, yattr)
    ylb = y_colmeta.axis_label
    yunt = y_colmeta.unit if y_colmeta.unit else ''
    
    if (xunt != 'a.u.') and (xunt != ''):
        x_scale, x_unit_prefix = xtils.get_autoscale(x.flatten())
    else:
        x_scale, x_unit_prefix = 1, ''
    if (yunt != 'a.u.') and (yunt != ''):
        y_scale, y_unit_prefix = xtils.get_autoscale(y.flatten())
    else:
        y_scale, y_unit_prefix = 1, ''
    
    fig, ax = xtils.ensure_fig_ax(fig, ax)
    pctrl = PlotCtrl(
        x_scale=x_scale,
        x_label=xlb,
        x_unit = x_unit_prefix+xunt,
        
        y_scale=y_scale,
        y_label=ylb,
        y_unit = y_unit_prefix+yunt,
        
        data_label=f'step={step:d}',
        unit_brk='[]',
        )
    if not allow_const_y:
        y_at_step = y[step]
    else:
        y_at_step = y[step] if y.shape[0] > 1 else y[0]
    xtils.plt.plot(x, y_at_step, pc=pctrl, fig=fig, ax=ax,  **pltkwargs)
    return fig, ax

def statistics_at_z(fname, z):
    gmr = MainResults(fname)
    t = gmr.t_from_s
    intfar, _ = gmr.get_data_at_z('intfar', z = z)
    ww, fspec = gmr.get_spectrum(z = z)
    freq_peak = ww[fspec==np.max(fspec)][0]
    ids = np.argsort(t)
    i1d = Intensity1D(x=t[ids], I=intfar[ids])
    sigma_t = i1d.rms_width()['sigma']
    fwhm = i1d.fwhm()['width']
    energy, _ = gmr.get_data_at_z('zenergy', z=z)
    return {
        f'peak_frequency@{z:.2f}m': freq_peak,
        f'sigma_t@{z:.2f}m' : sigma_t,
        f'fwhm@{z:.2f}m' : fwhm,
        f'energy@{z:.2f}m' : energy,
        }
    
def statistics_at_max(fname, ratio2max=1):
    gmr = MainResults(fname)
    z, _ = maximum_from_left(gmr.zplot, gmr.zenergy, ratio2max)
    res = {}
    stat_z = statistics_at_z(fname, z)
    for k, v in stat_z.items():
        attrname, _ = k.split('@')
        if not attrname.endswith('energy'):
            nkey = attrname+f'@{ratio2max*100:.0f}%_max_energy'
            res.update({nkey:v})
    res.update(
        {f'z@{ratio2max*100:.0f}%_max_energy': z}
        )
    return res

def statistics_maxs(fname):
    gmr = MainResults(fname)
    max_energy = np.max(gmr.zenergy)
    max_power = np.max(gmr.zpower)
    ppower = np.max(gmr.power, axis = 1)
    max_ppower = np.max(ppower)
    return {
        'max_energy': max_energy,
        'max_power': max_power,
        'max_ppower':max_ppower
        }


def stat_one(fname, zs=[], ratios2max=[]):
    res = dict()
    res.update(statistics_maxs(fname))
    if zs:
        for z in zs:
            res.update(statistics_at_z(fname, z))
    if ratios2max:
        for ratio in ratios2max:
            res.update(statistics_at_max(fname, ratio))
    return res


def fast_dump(fname, nsteps=1, th_cur=1e-2, th_wl=1e-2, backend='agg'):
    gmr = MainResults(fname)
    case_dir = os.path.dirname(gmr.h5_path)
    lambda0 = gmr.g_lambdaref
    os.makedirs(os.path.join(case_dir, 'results'), exist_ok=True)
    with use_backend(backend):
        step_idx_z = int(np.ceil(len(gmr.zplot)/nsteps))
        zids_loc = np.arange(len(gmr.zplot)-1, 0, -step_idx_z)[::-1]
        #--------------plot current & bunching-------------
        fig1, axes1 = xtils.new_subplots(nsteps, base_size=(4, 3),
                                       layout='constrained',
                                       )
        axes1 = np.asarray([axes1])
        axes1 = axes1.flatten()
        xmins, xmaxs = np.zeros(nsteps), np.zeros(nsteps)
        for idx in range(nsteps):
            z_idx = zids_loc[idx]
            zevo_line(gmr, z_idx, xattr='slice_num', yattr='current',
                      fig=fig1, ax=axes1[idx], allow_const_y=True,
                      color='red', linestyle='solid')
            ax_t_loc = axes1[idx].twinx()
            zevo_line(gmr, z_idx, xattr='slice_num', yattr='bunching',
                      fig=fig1, ax=ax_t_loc, allow_const_y=False,
                      color='blue', linestyle='solid')
            axes1[idx].set_title(f'z = {gmr.zplot[z_idx]:.3f}m')
            xmins[idx], xmaxs[idx], _ = focus_xlim_on_y_threshold(ax=ax_t_loc, threshold_rel=th_cur, set_xlim=False)
        xmin = xmins.min()
        xmax = xmaxs.max()
        for ax in axes1:
            ax.set_xlim((xmin, xmax))
        fig1.savefig(os.path.join(case_dir, 'results','current_bunching.png'))
        #--------------plot specturm-----------------------
        fig2, axes2 = xtils.new_subplots(nsteps, base_size=(4, 3),
                                       layout='constrained',
                                       )
        axes2 = np.asarray([axes2])
        axes2 = axes2.flatten()
        xmins, xmaxs = np.zeros(nsteps), np.zeros(nsteps)
        for idx in range(nsteps):
            z_idx = zids_loc[idx]
            zevo_line(gmr, z_idx, xattr='wavelength_spectra_wl', yattr='wavelength_spectra_int',
                      fig=fig2, ax=axes2[idx], allow_const_y=False,
                      # color='red', linestyle='solid',
                      )
            axes2[idx].set_title(f'z = {gmr.zplot[z_idx]:.3f}m')
            xmins[idx], xmaxs[idx], _ = focus_xlim_on_y_threshold(ax=axes2[idx], threshold_rel=th_wl, set_xlim=False)
        xmin = xmins.min()
        xmax = xmaxs.max()
        for ax in axes2:
            ax.set_xlim((xmin, xmax))
        fig2.savefig(os.path.join(case_dir, 'results','wavelength_spectrum.png'))
        
        #--------------plot pulse energy-------------------
        fig3, ax3 = xtils.new_subplots(1, base_size=(4,3),
                                       layout='constrained')
        fig, ax3 = zevo_stat(fname, yattr='zenergy', fig=fig3, ax=ax3)
        ax3.set_yscale('log')
        ax3.grid(True)
        ax3.set_title(f'Max. = {np.max(gmr.zenergy):.3e} J')
        fig3.savefig(os.path.join(case_dir, 'results','energy.png'))
        
        #--------------plot peak power---------------------
        fig4, ax4 = xtils.new_subplots(1, base_size=(4,3),
                                       layout='constrained')
        fig, ax4 = zevo_stat(fname, yattr='peakpower', fig=fig4, ax=ax4)
        ax4.set_yscale('log')
        ax4.grid(True)
        ax4.set_title(f'Max. = {np.max(gmr.peakpower):.3e} W')
        fig4.savefig(os.path.join(case_dir, 'results','peakpower.png'))
    
    




















