#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 16:56:28 2026

@author: duoxup
"""

from .dictx import CaseInsensitiveDict as dictX
from .namelist import Namelist, Namelists

defaults = dictX(pitz=dictX())
defaults['pitz'] = dictX(generator=Namelists(), astra=Namelists(), genesis=Namelists())
defaults['pitz']['generator'].update(Input=Namelist())
defaults['pitz']['astra'].update(NewRun=Namelist(), Charge=Namelist(), \
                             Cavity=Namelist(), Solenoid=Namelist(), Output=Namelist())
defaults['pitz']['genesis'].update(setup=Namelist(), time=Namelist(), importbeam=Namelist(), \
                             efield=Namelist(), field=Namelist(), track=Namelist())
#%% pitz astra defaults
defaults['pitz']['generator']['INPUT'].update(FNAME='temp.ini',
                 IPart=250000,
                 Species='electrons',
                 Q_total=-0.25,
                 Ref_Ekin=0,
                 LE=0.00055,
                 dist_pz='i',
                 Dist_z='g',
                 sig_clock=0.002547771,
                 Cathode=True,
                 Dist_x='r',
                 sig_x=0.3,
                 Dist_px='g',
                 Nemit_x=0,
                 Dist_y='r',
                 sig_y=0.3,
                 Dist_py='g',
                 Nemit_y=0,
                 C_sig_x=0,
                 C_sig_y=0,
                 Lprompt=False)
defaults['pitz']['astra']['NEWRUN'].update(Run=1,
                 Head='PITZ beam line simulation',
                 Distribution='temp.ini',
                 CathodeS=True,
                 Auto_Phase=True,
                 Track_All=True,
                 check_ref_part=False,
                 Lprompt=False,
                 Max_step=200000)
defaults['pitz']['astra']['CHARGE'].update(LSPCH=True,
                 Lmirror=True,
                 Nrad=40,
                 Nlong_in=50,
                 N_min=100,
                 Max_scale=0.05,
                 Max_count=20)
defaults['pitz']['astra']['CAVITY'].update(LEfield=True,
                 File_Efield1='/afs/ifh.de/group/pitz/data/lixiangk/work/apps/python3/3.9.18/lib64/python3.9/site-packages/interface/PITZsim/field-maps/gun52cavity.txt',
                 File_Efield2='/afs/ifh.de/group/pitz/data/lixiangk/work/apps/python3/3.9.18/lib64/python3.9/site-packages/interface/PITZsim/field-maps/CDS14_15mm.txt',
                 MaxE1=57.55088,
                 MaxE2=12.24552,
                 C_pos1=0,
                 C_pos2=2.675,
                 Nue1=1.3,
                 Nue2=1.3,
                 Phi1=0,
                 Phi2=0)
defaults['pitz']['astra']['SOLENOID'].update(LBfield=True,
                 File_Bfield1='/afs/ifh.de/group/pitz/data/lixiangk/work/apps/python3/3.9.18/lib64/python3.9/site-packages/interface/PITZsim/field-maps/gunsolenoidsPITZ.txt',
                 MaxB1=0.2152452,
                 S_pos1=0,
                 S_xrot1=0,
                 S_yrot1=0)
defaults['pitz']['astra']['OUTPUT'].update(Zstart=0,
                 Zstop=5.28,
                 Zemit=528,
                 Zphase=1,
                 RefS=True,
                 EmitS=True,
                 PhaseS=True,
                 TrackS=False,
                 LandFS=True,
                 C_EmitS=True,
                 LPROJECT_EMIT=True,
                 LOCAL_EMIT=False,
                 Screen1=5.28)
#%% pitz genesis defaults
defaults['pitz']['genesis']['SETUP'].update( rootname='g4.1',
                                             lattice='../../gen4lat.lat',
                                             beamline='THzBL',
                                             gamma0=33.381,
                                             lambda0=0.0001,
                                             delz=0.015,
                                             seed=1,
                                             npart=32768,
                                             nbins=16,
                                             one4one=False,
                                             shotnoise=True,
                                             field_global_stat=True,
                                             beam_global_stat=True,
                                             exclude_current_output=False)
defaults['pitz']['genesis']['TIME'].update(  s0=0,
                                             slen=0.0164,
                                             sample=1,
                                             time=True)
defaults['pitz']['genesis']['IMPORTBEAM'].update( file='scan.1.out.par.h5',
                                                  time=True)
defaults['pitz']['genesis']['EFIELD'].update(longrange=1,
                                             rmax=0.01,
                                             nz=5,
                                             nphi=1,
                                             ngrid=100)
defaults['pitz']['genesis']['FIELD'].update( power=0,
                                             phase=0,
                                             waist_size=0.3,
                                             waist_pos=0,
                                             dgrid=0.04,
                                             ngrid=501)
defaults['pitz']['genesis']['TRACK'].update( output_step=1,
                                             field_dump_step=0,
                                             beam_dump_step=0)