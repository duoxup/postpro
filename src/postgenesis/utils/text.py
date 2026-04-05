#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 16:11:56 2026

@author: duoxup
"""

def wrap_text(text, n):
    """
    Insert a newline character every n characters.

    Parameters
    ----------
    text : str
        Input text.
    n : int
        Number of characters per line.

    Returns
    -------
    str
        Wrapped text.
    """
    if n <= 0:
        raise ValueError("n must be a positive integer")

    return "\n".join(text[i:i+n] for i in range(0, len(text), n))


def args_dict_to_list(args: dict):
    x = [v for k, v in args.items()]
    return x
