#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 16:55:25 2026

@author: duoxup
"""

from .dictx import CaseInsensitiveDict as dictX
import numpy as np
import copy
        
class Namelist(dictX):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def to_lines(self, style=''):
        lines = ''
        for key, value in self.items():
            if _strIsNumber(key[-1]):
                if int(key[-1]) > 0:
                    key = key[:-1]+'({:.0f})'.format(int(key[-1]))
            if type(value) is not int and type(value) is not float and type(value) is not np.float64:
                if value is True:
                    value = 'true'
                elif value is False:
                    value = 'false'
                else:
                    if (style.lower() == 'astra') or (style.lower() == 'generator'):
                        value = '\'' + value + '\''
            else:
                pass
            lines += f' {key}={value}\n'
        return lines
    
    @classmethod
    def load_lines(cls, lines=''):
        kwargs = {}
        if type(lines) is not list:
            lines = lines.split('\n')
        for line in lines:
            key, value = line.strip().split('=')
            try:
                value = int(value)                
            except ValueError:
                try:
                    value = float(value)
                except:
                    pass
            except:
                pass
            if key.endswith(')'):
                key = key[:-3] + key[-2]
            kwargs.update({key: value})
        namelist = Namelist()
        namelist.update(**kwargs)
        return namelist
      
    def __deepcopy__(self, memo):
        new_dict = Namelist()
        memo[id(self)] = new_dict
        for key, value in self.items():
            new_dict[copy.deepcopy(key, memo)] = copy.deepcopy(value, memo)
        return new_dict
        
def _strIsNumber(x):
    if type(x) is bool:
        return False
    else:
        try:
            float(x)
            return True
        except:
            return False
    
class Namelists(dictX):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def update_by_another(self, nm2):
        for k in self:
            if k in nm2:
                self[k].update(**nm2[k])
    
    def to_lines(self, style=''):
        lines = ''
        for key, value in self.items():
            lines += f'&{key}\n'
            lines += value.to_lines(style)
            lines += '&end\n'
        return lines
    
    @classmethod
    def load_file(cls, file=''):
        if file:
            namelists = Namelists()
            emptyitemidx = []
            with open(file, 'r') as f:
                strcontent = f.read().split('&end')
            for i in range(len(strcontent)):
                strcontent[i] = strcontent[i].strip()
                if not strcontent[i]:
                    emptyitemidx += [i]
            for eidx in reversed(emptyitemidx):
                strcontent.pop(eidx)
            
            for strblock in strcontent:
                blockname = strblock.split('\n')[0].strip().strip('&')                
                namelist = Namelist.load_lines(strblock.split('\n')[1:])
                namelists.update(**{blockname: namelist})
            return namelists
        else:
            raise TypeError('filename has not been assigned')
