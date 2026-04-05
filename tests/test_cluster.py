#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 12:08:29 2026

@author: duoxup
"""

from postgenesis.cluster import cluster_fast_dump, cluster_statistics
from postgenesis.utils.dataframe import stat_dict_to_dataframe


if __name__ == '__main__':
    import os
    from multiprocessing import Pool
    
    
    # cdir = r'/lustre/fs25/group/pitz/duoxup/THzSuperRad/debug/'
    cdir = r'/lustre/fs25/group/pitz/duoxup/THzSuperRad/genesis/cluster00000201/'
    pool = Pool(processes=8)
    
    stat_dicts = cluster_statistics(cdir, zs=[0.13*3, 0.13*5], pool=pool)
    df = stat_dict_to_dataframe(stat_dicts)
    df.to_csv(os.path.join(cdir, '001.g4.000.out.h5.csv'), index=False)
    
    cluster_fast_dump(cdir, nsteps=4, pool=pool)
