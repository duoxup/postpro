#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 16:14:30 2026

@author: duoxup
"""
import matplotlib.pyplot as plt
from xtils import save_figure_auto_date
import pandas as pd
import os

from .utils.dataframe import get_column_start_with_key_in_dataframe
from .legacy.mappingforplot import mdp

figsize = [4, 3]
# figsize = [6, 4.5]
# figsize = [8, 6]
# figsize = [12, 9]

def add_plot_from_dataframe(ax, df, x_key, y_key, x_scale=1, y_scale=1, label=None, match_key_exactly= False, **kwargs):
    x_vector = get_column(df, x_key, match_key_exactly)
    y_vector = get_column(df, y_key, match_key_exactly)
    ax.plot(x_vector*x_scale, y_vector*y_scale, label=label)
    if 'yscale' in kwargs and kwargs['yscale'] == 'log':
        plt.yscale('log')
    if 'ylim' in kwargs:
        ax.set_ylim(kwargs['ylim'])
    
def add_plot_from_dataframe_g(ax, df, x_key, y_key, g_key=None, x_scale=1, y_scale=1, match_key_exactly= False, **kwargs):
    if g_key:
        g_list = df[g_key].unique().tolist()
        for g in g_list:
            sliced_df = df[df[g_key]==g]
            label = f'{g_key}={g:.2f}'
            add_plot_from_dataframe(ax, sliced_df, x_key, y_key, x_scale, y_scale, label=label, match_key_exactly=match_key_exactly, **kwargs)
    else:
        add_plot_from_dataframe(ax, df, x_key, y_key, x_scale, y_scale, label=None, match_key_exactly=match_key_exactly, **kwargs)

def plot_from_dataframe_g(df, x_key, y_key, g_key=None, x_scale=1, y_scale=1, match_key_exactly= False, **kwargs):
    fig, ax = plt.subplots(figsize=figsize, layout='constrained')
    add_plot_from_dataframe_g(ax, df, x_key, y_key, g_key, x_scale, y_scale, match_key_exactly=match_key_exactly, **kwargs)
    add_labels(x_key, y_key, x_scale, y_scale)
    if g_key:
        plt.legend(loc='best')
    return fig, ax

def plot_from_dataframe_g_t(df, x_key, y_key, g_key=None, t_key=None, x_scale=1, y_scale=1, match_key_exactly= False, save_folder=None, **kwargs):
    title_fontsize = 9
    if t_key:
        t_list = df[t_key].unique().tolist()
        for t in t_list:
            sliced_df = df[df[t_key]==t]
            fig, ax = plot_from_dataframe_g(sliced_df, x_key, y_key, g_key, x_scale, y_scale, match_key_exactly=match_key_exactly, **kwargs)
            title = get_title(sliced_df, x_key, y_key, t_key=t_key, t_value=t)
            plt.title(title, fontsize=title_fontsize)
            if save_folder is not None:
                save_figure_auto_date(sub_folder=save_folder)
    else:
        fig, ax = plot_from_dataframe_g(df, x_key, y_key, g_key, x_scale, y_scale, match_key_exactly=match_key_exactly, **kwargs)
        title = get_title(df, x_key, y_key, t_key=t_key, t_value=None)
        plt.title(title, fontsize=title_fontsize)
        if save_folder is not None:
            save_figure_auto_date(sub_folder=save_folder)
    return fig, ax

def plot_from_csv_in_multi_cluster(cluster_dir_list, fname_list, tag_list, x_key, y_key, x_scale=1, y_scale=1, match_key_exactly= False, save_folder=''): 
    if len(cluster_dir_list) != len(fname_list) or len(fname_list) != len(tag_list):
        raise ValueError('cluster_dir_list, fname_list, tag_list must have equal lengths')
    fig, ax = plt.subplots(figsize=figsize)
    for i in range(len(cluster_dir_list)):
        cluster_folder = cluster_dir_list[i]
        fname = fname_list[i]
        tag = tag_list[i]
        df = pd.read_csv(os.path.join(cluster_folder,fname))
        add_plot_from_dataframe_g(ax, df, x_key, y_key, match_key_exactly=match_key_exactly)
        
def get_column(df, key, match_key_exactly= False):
    if match_key_exactly:
        vector =  df[key]
    else:
        vector =  get_column_start_with_key_in_dataframe(df, key)
    return vector
        
def get_labels(x_key, y_key, x_scale=1, y_scale=1):
    x_key_modified, y_key_modified = x_key.rsplit('.', 1)[0].split('@')[0], y_key.rsplit('.', 1)[0].split('@')[0]
    x_dict, y_dict = mdp.get(x_key_modified), mdp.get(y_key_modified)
    xlabel_name = x_dict['plot_label'] if x_dict else x_key_modified
    xlabel_unit = scale_to_unit_prefix(x_scale) + x_dict['unit'] if x_dict else ''
    ylabel_name = y_dict['plot_label'] if y_dict else y_key_modified
    ylabel_unit = scale_to_unit_prefix(y_scale) + y_dict['unit'] if y_dict else ''
    return xlabel_name, xlabel_unit, ylabel_name, ylabel_unit

def add_labels(x_key, y_key, x_scale=1, y_scale=1):
    xlabel_name, xlabel_unit, ylabel_name, ylabel_unit = get_labels(x_key, y_key, x_scale, y_scale)
    xlabel_str = f'{xlabel_name} ({xlabel_unit})' if xlabel_unit else f'{xlabel_name}'
    ylabel_str = f'{ylabel_name} ({ylabel_unit})' if ylabel_unit else f'{ylabel_name}'
    plt.xlabel(xlabel_str)
    plt.ylabel(ylabel_str)
    
def get_title(df, x_key, y_key, t_key=None, t_value=None):
    x_key_modified, y_key_modified = x_key.rsplit('.', 1)[0].split('@')[0], y_key.rsplit('.', 1)[0].split('@')[0]
    t_key_modified = t_key.rsplit('.', 1)[0].split('@')[0] if t_key else ''
    x_dict, y_dict = mdp.get(x_key_modified), mdp.get(y_key_modified)
    t_dict = mdp.get(t_key_modified)
    title_str = ''
    x_title_str = x_dict.get('title_label') if x_dict else x_key_modified
    y_title_str = y_dict.get('title_label') if y_dict else y_key_modified
    title_str += y_title_str+ ' vs. ' + x_title_str
    if t_key and t_value:
        t_unit = t_dict.get('unit') if t_dict else ''
        title_str += f'\n {t_key} = {t_value} {t_unit}'
    return title_str

#for 2-layer pandas dataframe
def add_plot_m1d_from_2l_dataframe(ax, df, x_key, y_key, g_key = None, selected_g_value_list=[], x_scale=1, y_scale=1, match_key_exactly= False):
    yscale = 'log' if y_key == 'energy' else 'linear'
    if g_key:
        g_value_list = selected_g_value_list if selected_g_value_list else df[g_key].unique().tolist()
        for g_value in g_value_list:
            df_1 = df[df[g_key]==g_value]['df_1'].iloc[0]
            label = f'{g_value} '+mdp[g_key]['unit']
            add_plot_from_dataframe(ax, df_1, x_key, y_key, x_scale, y_scale, label=label, yscale=yscale, match_key_exactly=match_key_exactly)
    else:
        df_1 = df['df_1'].iloc[0]
        add_plot_from_dataframe(ax, df_1, x_key, y_key, x_scale, y_scale, yscale=yscale, match_key_exactly=match_key_exactly)
            
def plot_m1d_from_2l_dataframe(df, x_key, y_key, g_key = None, selected_g_value_list=[], x_scale=1, y_scale=1, match_key_exactly= False, save_folder=''):
    fig, ax = plt.subplots(figsize=figsize)
    add_plot_m1d_from_2l_dataframe(ax, df, x_key, y_key, g_key, selected_g_value_list, x_scale, y_scale, match_key_exactly=match_key_exactly)
    add_labels(x_key, y_key, x_scale, y_scale)
    title = get_title(df, x_key, y_key)
    plt.title(title)
    if g_key:
        plt.legend(loc='best')
    if save_folder:
        save_figure_auto_date(fname=title, sub_folder=save_folder)
        
        
def scale_to_unit_prefix(scale):
    if scale == 1e15:
        prefix = 'f'
    elif scale == 1e12:
        prefix = 'p'
    elif scale == 1e9:
        prefix = 'n'
    elif scale == 1e6:
        prefix = r'$\mu$'
    elif scale == 1e3:
        prefix = 'm'
    elif scale == 1:
        prefix = ''
    elif scale == 1e-3:
        prefix = 'k'
    elif scale == 1e-6:
        prefix = 'M'
    elif scale == 1e-9:
        prefix = 'G'
    elif scale == 1e-12:
        prefix = 'T'
    else:
        prefix = ''
        print('Invalid scale resulting in no matched prefix found.')
    return prefix