#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 16:08:03 2026

@author: duoxup
"""
import numpy as np

def maximum_from_left(x, y, percentage=1):
    if len(y) != len(x):
        raise ValueError('x and y must have equal length')
    if percentage > 1 or percentage < 0:
        raise ValueError('percentage must in between 0 and 1')
    y_max = max(y)
    y_target = y_max * percentage
    y_np = np.array(y)
    x_index = np.where(y_np >= y_target)[0]
    index_at_y_target = x_index[0]
    x_at_y_target = x[index_at_y_target]
    return x_at_y_target, y_target