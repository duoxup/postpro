#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr  4 22:49:30 2026

@author: duoxup
"""

from pathlib import Path
from postgenesis.cluster import cluster_fast_dump, cluster_statistics
from postgenesis.utils.dataframe import stat_dict_to_dataframe


if __name__ == '__main__':
    from multiprocessing import Pool
    
    
    cdir = Path('/lustre/fs25/group/pitz/duoxup/THz_ideal_machine/genesis/cluster00000003/')
    pool = Pool(processes=8)
    
    stat_dicts = cluster_statistics(cdir, zs=[0.13*3, 0.13*5], pool=None, version=2)
    df = stat_dict_to_dataframe(stat_dicts)
    df.to_csv(cdir / '001.g4.000.out.h5.csv', index=False)
    
    # cluster_fast_dump(cdir, nsteps=4, pool=pool)