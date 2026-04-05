#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  3 10:18:55 2025

@author: duoxup
"""
import interface as xki
from .dictx import CaseInsensitiveDict as dictX
from .dictx import merge_dicts
from .namelist import Namelist, Namelists
from .defaults import defaults
import numpy as np

usrparasmapping = dictX(Q_total = dictX(),
                BSA = dictX(),
                FWHM = dictX(),
                Rt = dictX(),
                Lt = dictX(),
                Rz = dictX(),
                Lz = dictX(),
                Ref_Ekin = dictX(),
                Cathode = dictX(),
                Nemit_x = dictX(),
                Nemit_y = dictX(),
                LE = dictX(),
                cor_Ekin = dictX(),
                Probe = dictX(),
                Dist_x = dictX(),
                Dist_y = dictX(),
                LSPCH = dictX(),
                P_gun = dictX(),
                MaxE_gun = dictX(),
                phi_gun = dictX(),
                P_booster = dictX(),
                MaxE_booster = dictX(),
                phi_booster = dictX(),
                solenoid = dictX(),
                LaserTran = dictX(),
                LaserTemp = dictX(),
                IPart = dictX(),
                sig_x = dictX(),
                C_sig_x = dictX(),
                sig_y = dictX(),
                C_sig_y = dictX(),
                FNAME = dictX(),
                sig_z = dictX(),
                C_sig_z = dictX(),
                sig_Ekin = dictX(),
                Dist_z = dictX(),
                dist_pz = dictX(),
                Distribution = dictX(),
                inputName = dictX(),
                outputName = dictX(),
                nproc = dictX(),
                Qscale = dictX(), 
                zscale = dictX(),
                bunch = dictX(), 
                Freq = dictX(),
                nperlambda = dictX(),
                useHammersley = dictX(),
                rootname = dictX(),
                lattice = dictX(),
                beamline = dictX(),
                gamma0 = dictX(),
                lambda0 = dictX(),
                delz = dictX(),
                seed = dictX(),
                seedidx = dictX(),
                npart = dictX(),
                nbins = dictX(),
                one4one = dictX(),
                shotnoise = dictX(),
                s0 = dictX(),
                slen = dictX(),
                sample = dictX(),
                timetime = dictX(),
                file = dictX(),
                timeipb = dictX(),
                longrange = dictX(),
                rmax = dictX(),
                nz = dictX(),
                nphi = dictX(),
                ngridef = dictX(),
                power = dictX(),
                phase = dictX(),
                waist_size = dictX(),
                waist_pos = dictX(),
                dgrid = dictX(),
                ngridf = dictX(),
                output_step = dictX(),
                field_dump_step = dictX(),
                beam_dump_step = dictX(),
                zbl = dictX(),
                zbu = dictX(),
                autotrim = dictX())
umap = usrparasmapping
for key, value in umap.items():
    value.update(name=key,
                 alias=key,
                 ratio2ast=1,
                 preprofunc=None,
                 plot_label=key,
                 title_label=key,
                 )
umap['Q_total'].update(program='generator', namelist='input', alias='Q', unit='pC', showdigits=0, ratio2ast = 1e-3, plot_label='Charge') #[nC] in ast.in
umap['BSA'].update(program='generator', namelist='input', name=None, alias='D', unit='mm', showdigits=1)
umap['FWHM'].update(program='generator', namelist='input', name='sig_clock', alias='L', unit='ps', showdigits=1, ratio2ast = 1/np.sqrt(2*np.log(2))/2*1e-3) #[ns] in gen.in
umap['Rt'].update(program='generator', namelist='input', unit='ps', showdigits=1, ratio2ast=1e-3) #[ns] in ast.in
umap['Lt'].update(program='generator', namelist='input', unit='ps', showdigits=1, ratio2ast=1e-3) #[ns] in ast.in
umap['Rz'].update(program='generator', namelist='input', unit='mm', showdigits=2) #[mm] in ast.in
umap['Lz'].update(program='generator', namelist='input', unit='mm', showdigits=2) #[mm] in ast.in
umap['Ref_Ekin'].update(program='generator', namelist='input', alias='E0', unit='MeV', showdigits=2)
umap['Cathode'].update(program='generator', namelist='input', alias='Cathode', unit='', showdigits=None)
umap['Nemit_x'].update(program='generator', namelist='input', alias='Nemitx', unit='mmmrad', showdigits=2)
umap['Nemit_y'].update(program='generator', namelist='input', alias='Nemity', unit='mmmrad', showdigits=2)
umap['LE'].update(program='generator', namelist='input', alias='LE', unit='keV', showdigits=2)
umap['cor_Ekin'].update(program='generator', namelist='input', alias='cor_E0', unit='keV', showdigits=2, plot_label='Correlated energy spread', title_label='Correlated energy spread')
umap['Probe'].update(program='generator', namelist='input', unit='', showdigits=None)
umap['Dist_x'].update(program='generator', namelist='input', unit='', showdigits=None)
umap['Dist_y'].update(program='generator', namelist='input', unit='', showdigits=None)
umap['LSPCH'].update(program='astra', namelist='charge', unit='', showdigits=None)
umap['P_gun'].update(program='astra', namelist='cavity', name=None, alias='PG', unit='MeV_c', showdigits=2)
umap['MaxE_gun'].update(program='astra', namelist='cavity', name='MaxE1', alias='E1', unit='MV_m', showdigits=2)
umap['phi_gun'].update(program='astra', namelist='cavity', name='Phi1', alias='phi1', unit='deg', showdigits=0, plot_label='Gun phase', title_label='Gun phase')
umap['P_booster'].update(program='astra', namelist='cavity', name=None, alias='PB', unit='MeV_c', showdigits=2)
umap['MaxE_booster'].update(program='astra', namelist='cavity', name='MaxE2', alias='E2', unit='MV_m', showdigits=2)
umap['phi_booster'].update(program='astra', namelist='cavity', name='Phi2', alias='phi2', unit='deg', showdigits=0, plot_label='Booster phase', title_label='Booster phase')
umap['solenoid'].update(program='astra', namelist='solenoid', name='MaxB1', alias='I', unit='A', showdigits=0, preprofunc=xki.I2B)
umap['LaserTran'].update(program='generator', namelist='input', name=None, alias='LTran', unit='', showdigits=None)
umap['LaserTemp'].update(program='generator', namelist='input', name=None, alias='LTemp', unit='', showdigits=None)
umap['IPart'].update(program='generator', namelist='input', unit='', showdigits=0, preprofunc=int)
umap['sig_x'].update(program='generator', namelist='input', unit='mm', showdigits=1)
umap['C_sig_x'].update(program='generator', namelist='input', unit='mm', showdigits=1)
umap['sig_y'].update(program='generator', namelist='input', unit='mm', showdigits=1)
umap['C_sig_y'].update(program='generator', namelist='input', unit='mm', showdigits=1)
umap['FNAME'].update(program='generator', namelist='input', unit='', showdigits=None)
umap['sig_z'].update(program='generator', namelist='input', unit='mm', showdigits=2)
umap['C_sig_z'].update(program='generator', namelist='input', unit='mm', showdigits=2)
umap['sig_Ekin'].update(program='generator', namelist='input', unit='keV', showdigits=2, plot_label='Uncorrelated energy spread', title_label='Uncorrelated energy spread')
umap['Dist_z'].update(program='generator', namelist='input', unit='', showdigits=None)
umap['dist_pz'].update(program='generator', namelist='input', unit='', showdigits=None)
umap['Distribution'].update(program='astra', namelist='newrun', unit='', showdigits=None)
umap['inputName'].update(program='genesis', namelist=None, name=None, unit='', showdigits=None)
umap['outputName'].update(program='genesis', namelist=None, name=None, unit='', showdigits=None)
umap['nproc'].update(program='genesis', namelist=None, unit='', showdigits=0)
umap['Qscale'].update(program='genesis', namelist=None, name=None, unit='', showdigits=2)
umap['zscale'].update(program='genesis', namelist=None, name=None, unit='', showdigits=2)
umap['bunch'].update(program='genesis', namelist=None, name=None, unit='', showdigits=2)
umap['Freq'].update(program='genesis', namelist=None, name=None, alias='f', unit='THz', showdigits=0)
umap['nperlambda'].update(program='genesis', namelist=None, name=None, unit='', showdigits=0)
umap['useHammersley'].update(program='genesis', namelist=None, name=None, unit='', showdigits=None)
umap['rootname'].update(program='genesis', namelist='setup', unit='', showdigits=None)
umap['lattice'].update(program='genesis', namelist='setup', unit='', showdigits=None)
umap['beamline'].update(program='genesis', namelist='setup', unit='', showdigits=None)
umap['gamma0'].update(program='genesis', namelist='setup', unit='', showdigits=2)
umap['lambda0'].update(program='genesis', namelist='setup', unit='', showdigits=5)
umap['delz'].update(program='genesis', namelist='setup', unit='', showdigits=3)
umap['seed'].update(program='genesis', namelist='setup', unit='', showdigits=0)
umap['seedidx'].update(program='genesis', namelist=None, unit='', showdigits=0)
umap['npart'].update(program='genesis', namelist='setup', unit='', showdigits=0)
umap['nbins'].update(program='genesis', namelist='setup', unit='', showdigits=0)
umap['one4one'].update(program='genesis', namelist='setup', unit='', showdigits=None)
umap['shotnoise'].update(program='genesis', namelist='setup', unit='', showdigits=None)
umap['s0'].update(program='genesis', namelist='time' , unit='', showdigits=0)
umap['slen'].update(program='genesis', namelist='time', unit='', showdigits=4)
umap['sample'].update(program='genesis', namelist='time', unit='', showdigits=0)
umap['timetime'].update(program='genesis', namelist='time', unit='', showdigits=None)
umap['file'].update(program='genesis', namelist='importbeam', unit='', showdigits=None)
umap['timeipb'].update(program='genesis', namelist='importbeam', unit='', showdigits=None)
umap['longrange'].update(program='genesis', namelist='efield', alias='LSC', unit='', showdigits=0, preprofunc=int)
umap['rmax'].update(program='genesis', namelist='efield', unit='', showdigits=2)
umap['nz'].update(program='genesis', namelist='efield', unit='', showdigits=0)
umap['nphi'].update(program='genesis', namelist='efield', unit='', showdigits=0)
umap['ngridef'].update(program='genesis', namelist='efield', unit='', showdigits=0)
umap['power'].update(program='genesis', namelist='field', unit='', showdigits=0)
umap['phase'].update(program='genesis', namelist='field', unit='', showdigits=0)
umap['waist_size'].update(program='genesis', namelist='field', unit='', showdigits=2)
umap['waist_pos'].update(program='genesis', namelist='field', unit='', showdigits=2)
umap['dgrid'].update(program='genesis', namelist='field', unit='', showdigits=2)
umap['ngridf'].update(program='genesis', namelist='field', name='ngrid', unit='', showdigits=0)
umap['output_step'].update(program='genesis', namelist='track', unit='', showdigits=0)
umap['field_dump_step'].update(program='genesis', namelist='track', unit='', showdigits=0)
umap['beam_dump_step'].update(program='genesis', namelist='track', unit='', showdigits=0)
umap['zbl'].update(program='genesis', namelist=None, unit='um', showdigits=3)
umap['zbu'].update(program='genesis', namelist=None, unit='um', showdigits=3)
umap['autotrim'].update(program='genesis', namelist=None, unit='', showdigits=None)

class usrparas(dictX):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def to_jobname(self, connector1 = '-', connector2 = '-', global_digits=-1, default_digits=3, NameList = [], showunit:bool = True):
        if not NameList:
            NameList = self.keys()
        parastr = []
        for k, v in self.items():
            if k in NameList:
                default_show_digits = umap[k]['showdigits'] if k in umap else None
                # if global_digits is not None and default_show_digits is not None:
                #     dgs = global_digits if global_digits >= 0 else default_show_digits
                #     formatstr = '{:.%df}' % dgs
                # else:
                #     formatstr = '{}'
                if type(v) is str:
                    formatstr = '{}'
                else:
                    if global_digits is not None and global_digits >= 0:
                        dgs = global_digits
                        formatstr = '{:.%df}' % dgs
                    elif default_show_digits is not None:
                        dgs = default_show_digits
                        formatstr = '{:.%df}' % dgs
                    elif default_digits is not None and default_digits>=0:
                        dgs = default_digits
                        formatstr = '{:.%df}' % dgs
                    else:
                        formatstr = '{}'
                unitstr = umap[k]['unit'] if k in umap and showunit else ''
                aliasstr = umap[k]['alias'] if k in umap else k
                parastr += [(aliasstr + connector1 + formatstr + unitstr).format(v)]
        jobname = connector2.join(parastr)
        return jobname
    
    def slice_by_program(self, program):
        dict1 = usrparas()
        for k, v in self.items():
            if umap[k]['program'] == program:
                dict1.update({k: v})
        return dict1
    
    def slice_by_namelist(self, namelist):
        dict1 = usrparas()
        for k, v in self.items():
            if umap[k]['namelist'] == namelist:
                dict1.update({k: v})
        return dict1
    
    def slice_by_names(self, *names):
        dict1 = usrparas()
        for k, v in self.items():
            if k in names:
                dict1.update({k: v})
        return dict1
        
    def to_namelists(self, filenamingparams:list = ['BSA','FWHM','IPart']):
        kparas1 = usrparas()
        ukparas = usrparas()
        for k, v in self.items():
            if k in umap and umap[k]['name'] is not None:
                kparas1.update({k: v})
            else:
                ukparas.update({k: v})
        kdict = _known_paras_to_namelist(kparas1)
        spusrparas = self._parsespecialparas(ukparas)
        spdict = _known_paras_to_namelist(spusrparas)
        if 'FNAME' in self:
            FNAME = self['FNAME']
            Distribution = self['FNAME']
        else:
            sliced = self.slice_by_names(*filenamingparams)
            FNAME = sliced.to_jobname()+'.ini'
            Distribution = sliced.to_jobname()+'.ini'
        nparas = usrparas(FNAME=FNAME,
                      Distribution=Distribution)
        ndict = _known_paras_to_namelist(nparas)
        merge_dicts(kdict, spdict)
        merge_dicts(kdict, ndict)
        return kdict
    
    def create_in_file(self, infilename='gen.in', setup='pitz', program='generator', filenamingparams=['BSA','FWHM','IPart']):
        paras = Namelists(**defaults[setup][program])
        anparas = self.to_namelists(filenamingparams=filenamingparams)[program]
        paras.update_by_another(anparas)
        inlines = paras.to_lines(program)
        with open(infilename, 'w') as file:
            file.write(inlines)
        if program.lower() == 'generator':
            return paras['Input']['FNAME']
        elif program.lower() == 'astra':
            zstop = paras['Output']['Zstop']
            run = paras['NewRun']['Run']
            return 'ast.{:.0f}.{:.0f}'.format(zstop*100, run)

    def _parsespecialparas(self, specialparas: dictX):
        spusrparas = usrparas()
        IsCathode = self['Cathode'] if 'Cathode' in self else True
        for k, v in specialparas.items():
            if k.lower() == 'lasertran':
                if isinstance(v, str):
                    if str(v).lower() == 'gaussian':
                        temp_v = 0
                    elif str(v).lower() == 'uniform':
                        temp_v = 1
                else:
                    temp_v = v
                if temp_v == 0:
                    if 'BSA' in self:
                        sig_x = self['sig_x'] if 'sig_x' in self else 1
                        sig_y = self['sig_y'] if 'sig_y' in self else 1
                        spusrparas.update(Dist_x='2',Dist_y = '2',sig_x=sig_x, C_sig_x=self['BSA']/2., sig_y=sig_y, C_sig_y=self['BSA']/2.)
                    else:
                        raise ValueError('BSA not assigned for Gaussian distribution')
                elif temp_v == 1:
                    if 'BSA' in self:
                        spusrparas.update(sig_x=self['BSA']/4., C_sig_x=0, sig_y=self['BSA']/4., C_sig_y=0)
                    else:
                        raise ValueError('BSA not assigned for Uniform distribution')
                else:
                    raise ValueError('Unknown transverse laser distribution.')
            elif k.lower() == 'lasertemp':
                if isinstance(v, str):
                    if str(v).lower() == 'gaussian':
                        temp_v = 0
                    elif str(v).lower() == 'plateau':
                        temp_v = 1
                else:
                    temp_v = v
                if temp_v == 0:
                    pass
                elif temp_v == 1:
                    if IsCathode:
                        Lt = self['FWHM']
                        Rt = self['Rt'] if 'Rt' in self else Lt/10
                        Dist_z = 'p'
                        spusrparas.update(Dist_z=Dist_z, Lt=Lt, Rt=Rt)
                    else:
                        Lz = self['Lz']
                        Rz = self['Rz'] if 'Rz' in self else Lz/10
                        Dist_z = 'p'
                        spusrparas.update(Dist_z=Dist_z, Lz=Lz, Rz=Rz)
            elif k.lower() == 'p_gun':
                phi_gun = self['phi_gun']
                P_gun = self['p_gun']
                MaxE_gun = xki.get_MaxE_gun(phi_gun, P_gun)
                spusrparas.update(MaxE_gun=MaxE_gun)
            elif k.lower() == 'p_booster':
                P_gun = self['p_gun']
                phi_gun = self['phi_gun']
                P_booster = self['p_booster']
                phi_booster = self['phi_booster']
                MaxE_gun = xki.get_MaxE_gun(phi_gun, P_gun)
                MaxE_booster =  xki.get_MaxE_booster(MaxE_gun, phi_gun, phi_booster, P_booster)
                spusrparas.update(MaxE_booster=MaxE_booster)
            else:
                pass #DX20062025
        return spusrparas
    
def _known_paras_to_namelist(kparas: usrparas):
    dict1 = dictX()
    programs = set([umap[k]['program'] for k in kparas])
    for p in programs:
        paras = kparas.slice_by_program(p)
        nls = Namelists()
        nms = set([umap[k]['namelist'] for k in paras])
        for nm in nms:
            nl = Namelist()
            nmparas = paras.slice_by_namelist(nm)
            for k, v in nmparas.items():
                if umap[k]['preprofunc'] is not None:
                    preprofunc = umap[k]['preprofunc']
                    v = preprofunc(v)
                if umap[k]['showdigits'] is not None:
                    v = v * umap[k]['ratio2ast']
                nl.update({umap[k]['name']: v})
            nls.update({umap[k]['namelist']: nl})
        dict1.update({umap[k]['program']: nls})
    return dict1