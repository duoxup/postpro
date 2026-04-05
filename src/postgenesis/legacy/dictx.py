#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 16:51:34 2026

@author: duoxup
"""

import copy

class common_constant():
    def __init__(self):
        self.c = 299792458 #[m/s]
        self.m0 = 9.1093837e-31 #[kg]
        self.e0 = 1.60217663e-19 #[C]
        
class CaseInsensitiveDict(dict):
    """Dictionary with case-insensitive key access while preserving original key case"""
    
    def __init__(self, *args, **kwargs):
        self._key_map = {}
        super().__init__()
        self.update(*args, **kwargs)
        
    def __setitem__(self, key, value):
        lower_key = key.lower()
        
        if lower_key in self._key_map:
            original_key = self._key_map[lower_key]
            # if original_key in super():  # Check if the key exists in the super dictionary. Advice from gemini
            super().__delitem__(original_key)
            
        super().__setitem__(key, value)
        self._key_map[lower_key] = key
        
    def __getitem__(self, key):
        return super().__getitem__(self._key_map[key.lower()])
    
    def __delitem__(self, key):
        lower_key = key.lower()
        original_key = self._key_map[lower_key]
        super().__delitem__(original_key)
        del self._key_map[lower_key]
        
    def __contains__(self, key):
        return key.lower() in self._key_map
    
    def __deepcopy__(self, memo):
        new_dict = CaseInsensitiveDict()
        memo[id(self)] = new_dict
        for key, value in self.items():
            new_dict[copy.deepcopy(key, memo)] = copy.deepcopy(value, memo)
        return new_dict
    
    def keys(self):
        return CaseInsensitiveKeysView(self)
    
    def get(self, key, default=None):
        lower_key = key.lower()
        original_key = self._key_map.get(lower_key, key)
        return super().get(original_key, default)
    
    def get_with_start(self, key, default=None):
        full_lower_key = self._find_key_start_with(key)
        original_key = self._key_map.get(full_lower_key)
        return super().get(original_key, default)
    
    
    def _find_key_start_with(self, key_start):
        lower_key_start = key_start.lower()
        found_keys_list = []
        for key in self._key_map:
            if key.startswith(lower_key_start):
                found_keys_list += [key]
        if len(found_keys_list) == 0:
            raise ValueError(f'No key start with {key_start}')
        elif len(found_keys_list) > 1:
            raise ValueError(f'Multiple keys found start with {key_start}')
        else:
            return found_keys_list[0]
            
    def pop(self, key, default=None):
        lower_key = key.lower()
        original_key = self._key_map.pop(lower_key, key)
        return super().pop(original_key, default) if original_key in self else default
    
    def update(self, other=None, **kwargs):
        if other:
            for k, v in (other.items() if hasattr(other, 'keys') else other):
                self[k] = v
        for k in kwargs:
            self[k] = kwargs[k]
    
    def items(self):
        return CaseInsensitiveItemsView(self)


class CaseInsensitiveKeysView:
    """Case-insensitive view of dictionary keys"""
    def __init__(self, parent_dict):
        self._parent = parent_dict
        
    def __contains__(self, key):
        return key.lower() in self._parent._key_map
    
    def __iter__(self):
        return iter(self._parent._key_map.values())
    
    def __len__(self):
        return len(self._parent)
    
    def __repr__(self):
        return f"CaseInsensitiveKeysView({list(self)})"


class CaseInsensitiveItemsView:
    """Case-insensitive view of dictionary items"""
    def __init__(self, parent_dict):
        self._parent = parent_dict
        
    def __contains__(self, item):
        key, value = item
        return (key.lower() in self._parent._key_map) and (self._parent[key] == value)
    
    def __iter__(self):
        for key in self._parent._key_map.values():
            yield (key, self._parent[key])
    
    def __len__(self):
        return len(self._parent)
    
    def __repr__(self):
        return f"CaseInsensitiveItemsView({list(self)})"