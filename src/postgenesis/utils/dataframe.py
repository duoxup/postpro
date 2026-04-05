#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 16:05:16 2026

@author: duoxup
"""

import pandas as pd
import numpy as np

from typing import Sequence

def get_column_start_with_key_in_dataframe(df, key):
    lower_key_start = key.lower()
    found_indice_list = []
    for index in df.columns:
        if index.lower().startswith(lower_key_start):
            found_indice_list += [index]
    if len(found_indice_list) == 0:
        raise ValueError(f'No column index start with {key}')
    elif len(found_indice_list) > 1:
        raise ValueError(f'Multiple column indice found start with {key}')
    else:
        found_index = found_indice_list[0]
        return df[found_index]
    
def stat_dict_to_dataframe(dict_seq: Sequence[dict]):
    keys = dict_seq[0].keys()
    v_list = []
    for stat_dict in dict_seq:
        if stat_dict.keys() != keys:
            raise ValueError('All dicts in dict_seq must have same keys.')
        v_list.append(list(stat_dict.values()))
    header = list(keys)
    v_array = np.array(v_list)
    df = pd.DataFrame(v_array, columns=header)
    return df