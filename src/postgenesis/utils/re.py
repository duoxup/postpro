#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  1 11:14:22 2025

@author: duoxup
"""


import re
from pathlib import Path
from typing import Union
_num_re = re.compile(r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$')

def _parse_value(s: str):
    s = s.strip()
    low = s.lower()
    if low == "true":  return True
    if low == "false": return False
    if _num_re.match(s):
        v = float(s)
        if re.match(r'^[+-]?\d+$', s):
            try:
                return int(s)
            except Exception:
                return v
        return v
    return s  

def get_undulator_params(file_path: Union[str, Path], line_key: str) -> dict:
    text = Path(file_path).read_text(encoding="utf-8")

    undu_pat = re.compile(r'^(\w+):\s*undulator\s*=\s*\{([^}]*)\};', re.M)
    undulators = {name: params for name, params in undu_pat.findall(text)}

    line_pat = re.compile(r'^(\w+):\s*line\s*=\s*\{([^}]*)\};', re.M)
    lines = {name: [t.strip() for t in body.split(',')] for name, body in line_pat.findall(text)}

    if line_key not in lines:
        raise KeyError(f"Line '{line_key}' not found.")

    for token in lines[line_key]:
        if token in undulators:
            params_str = undulators[token]
            kvs = [p.strip() for p in params_str.split(',') if p.strip()]
            out = {}
            for kv in kvs:
                if '=' not in kv:
                    continue
                k, v = kv.split('=', 1)
                out[k.strip()] = _parse_value(v)
            return out

    raise KeyError(f"No undulator referenced by line '{line_key}'.")
    
_SLICE_RE = re.compile(r"^\s*#\s*of\s*slices:\s*(\d+)\b", re.IGNORECASE)

def max_slice_index(path: Union[str, Path]) -> int:
    """
    Return the maximum slice index found in a text file containing lines like:
    '# of slices:  21 , current = ...'

    Raises:
        ValueError: if no slice indices are found.
    """
    path = Path(path)
    max_idx = None

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = _SLICE_RE.match(line)
            if m:
                idx = int(m.group(1))
                max_idx = idx if max_idx is None else max(max_idx, idx)

    if max_idx is None:
        raise ValueError(f"No slice indices found in: {path}")
    return max_idx

def get_step_of_dump(fname: str, prefix: str = 'g4.000', suffix='par.h5'):
    pat = re.compile(rf"^{re.escape(prefix)}\.(\d+)\.{re.escape(suffix)}$")
    try:
        step_par_dump = int(pat.match(fname).group(1))
        return step_par_dump
    except:
        raise ValueError(f'cannot parse a number from \'{fname}\' with pattern: \'{prefix}.*.{suffix}\'')



if __name__  == '__main__':
    fname = 'g4.000.6.par.h5'
    step = get_step_of_dump(fname, prefix='g4.000', suffix='par.h5')
    
    
    
    
    
    
    
    
    
    