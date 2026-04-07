#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  6 19:00:28 2026

@author: duoxup
"""

from pathlib import Path

from postgenesis.vizdfscan import ColumnMetaRegistry, make_registry

workdir = Path(r'/afs/ifh.de/group/pitz/data/duoxup/sim1/pyS')
fname_old = 'colmeta_4.json'
fname_new = 'colmeta_5.json'

metas= ColumnMetaRegistry.from_json(workdir / fname_old)

"""
Example:
spec = {
    "Q_total": {"unit": "pC", "axis_label": "Bunch charge", "alias": "Q", "scale": 1e12, "digits_show": 2},
    "sig_z": {"unit": "mm", "axis_label": "Bunch length (rms)", "scale": 1e3, "digits_show": 2},
}
"""

new_metas = make_registry({
    'scr_pslc_cor_pz':{'unit': 'eV/c',
                       'axis_label':'Correlated longitudinal momentum spread',
                       'alias':r'$\sigma_{pz}^{cor}$',
                       'digits_show': 2,
                       },
    'oth_q':{'unit': 'pC',
             'axis_label':'Charge',
             'alias':'$Q$',
             'digits_show': 0,
             },
    
    'oth_lambda0_um':{'unit': '$mu m$',
                      'axis_label':'Wavelength',
                      'alias':r'$\lambda_0$',
                      'digits_show': 0,
                      },
    'oth_beta_x0':{'unit': None,
                   'axis_label':r'$\beta_{x0}/\beta_{eq}$',
                   'alias':r'$\beta_{x0}/\beta_{eq}$',
                   'digits_show': 3,
                   },
    'gen_input_cor_ekin':{'unit': 'keV',
                          'axis_label':'Correlated energy spread',
                          'alias':r'$\sigma_E^{cor}$',
                          'digits_show': 0,
                          },
    'gen_input_sig_z':{'unit': 'mm',
                       'axis_label':'Bunch length',
                       'alias':r'\sigma_z',
                       'digits_show': 2,
                       },
    'oth_i_peak':{'unit': 'A',
                  'axis_label':'Peak current',
                  'alias':r'$I_{peak}$',
                  'digits_show': 2,
                  },
    'oth_width_mb':{'unit': None,
                  'axis_label':r'$w_{mb}/\lambda_0$',
                  'alias':r'$w_{mb}/\lambda_0$',
                  'digits_show': 2,
                  },
    })

for meta in new_metas._metas.values():
    metas.add(meta)

metas.to_json(workdir/ fname_new)