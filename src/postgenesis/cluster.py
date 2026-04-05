#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 17:04:29 2026

@author: duoxup
"""
import os
# import xtils
import json
import pandas as pd

from tqdm import tqdm
from pathlib import Path

from xtils.io.copyfiles import list_directories
from .singlecase import fast_dump, stat_one

def _get_case_folders(cluster_dir: Path):
    df = pd.read_csv(cluster_dir / 'cases.csv')
    directories = df['directory'].to_list()
    return directories

def wrapper1(args):
    return fast_dump(*args)


def wrapper2(args):
    caseargs, mr_fname, zs, ratios2max = args
    stat = stat_one(mr_fname, zs, ratios2max)
    res = caseargs.copy()
    res.update(**stat)
    return res

def cluster_fast_dump(cluster_dir, nsteps=4, pool=None):
    if not os.path.lexists(cluster_dir):
        raise FileNotFoundError('Cluster directory not found.')
    cfs_fname = os.path.join(cluster_dir, 'CasesInCluster.txt')
    if os.path.lexists(cfs_fname):
        with open(cfs_fname, 'r') as f:
            casefolders = f.read().split('\n')
    else:
        casefolders = list_directories(cluster_dir)
        
    mr_fnames = [os.path.join(cluster_dir, folder, 'g4.000.out.h5')
                 for folder in casefolders]
    args_list = [(mr_fname, nsteps) for mr_fname in mr_fnames]
    if pool:
        for _ in tqdm(pool.imap_unordered(wrapper1, args_list),
                        total=len(casefolders)):
            pass
    else:
        for idx in tqdm(range(len(casefolders))):
            args = args_list[idx]
            wrapper1(args)
        
        
    
def cluster_statistics_v1(cluster_dir, zs=[], ratios2max=[1, 0.9, 0.8], pool=None):
    if not os.path.lexists(cluster_dir):
        raise FileNotFoundError('Cluster directory not found.')
    cfs_fname = os.path.join(cluster_dir, 'CasesInCluster.txt')
    cargs_fname = os.path.join(cluster_dir, 'CasesInCluster.json')
    with open(cfs_fname, 'r') as f:
        casefolders = f.read().split('\n')
    with open(cargs_fname, 'r') as f:
        caseargs_list = json.load(f)
        
    mr_fbasename = 'g4.000.out.h5'
    
    args_list = []
    for idx in range(len(casefolders)):
        caseargs = caseargs_list[idx]
        casefolder = casefolders[idx]
        mr_fname = os.path.join(cluster_dir, casefolder, mr_fbasename)
        args_list.append((caseargs, mr_fname, zs, ratios2max))
        
    stat_dict_seq = []
    if pool:
        for res in tqdm(pool.imap(wrapper2, args_list),
                        total=len(casefolders)):
            stat_dict_seq.append(res)
    else:
        for idx in tqdm(range(len(casefolders))):
            stat_dict_seq.append(wrapper2(args_list[idx]))
    return stat_dict_seq

def cluster_statistics_v2(cluster_dir, zs=[], ratios2max=[1, 0.9, 0.8], pool=None):
    cluster_dir = Path(cluster_dir)
    if not cluster_dir.exists():
        raise FileNotFoundError('Cluster directory not found.')
    mr_fbasename = 'outputs/g4.000.out.h5'
    
    df = pd.read_csv(cluster_dir / 'cases.csv')
    df_params = df.drop(columns=['case_id', 'directory'])
    
    args_list = []
    for idx in range(len(df)):
        casefolder = df.loc[idx]['directory']
        caseargs = df_params.loc[idx].to_dict()
        mr_fname = cluster_dir / casefolder / mr_fbasename
        args_list.append((caseargs, mr_fname, zs, ratios2max))
    
    stat_dict_seq = []
    if pool:
        for res in tqdm(pool.imap(wrapper2, args_list),
                        total=len(df)):
            stat_dict_seq.append(res)
    else:
        for idx in tqdm(range(len(df))):
            stat_dict_seq.append(wrapper2(args_list[idx]))
    return stat_dict_seq

def cluster_statistics(cluster_dir, zs=[], ratios2max=[1, 0.9, 0.8], pool=None,
                       version = 1):
    match version:
        case 1:
            return cluster_statistics_v1(cluster_dir, zs, ratios2max, pool)
        case 2:
            return cluster_statistics_v2(cluster_dir, zs, ratios2max, pool)
        case _:
            raise NotImplementedError(f'Version {version} is not implemented.')
        









