#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 15:55:05 2026

@author: duoxup
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  5 11:19:26 2025

@author: duoxup
"""

import h5py
import numpy as np

from typing import Optional, List, Tuple, Union
import os
from pathlib import Path

from .utils.re import max_slice_index

from scipy.constants import c as c0
from dstrux import Intensity1D, H5Proxy

def calcSpectrum_xk(inten, phase = None, lambda0 = 100e-6, sample = 1, freq0 = None):
    '''
    Calculate the spectrum from samples

    Parameters
    ----------
    inten : 1D or 2D array
        Intensity of samples of the signal. In the case of 2D, the first dimension 
        is along the slices and the second dimension is along the undulator. 
        Can also be the complex fields, then `phase` is not needed.
    phase : 1D or 2D array
        Phases of samples of the signal. The default is None, if the amp is given as complex fields.
    lambda0 : double, optional
        Seperation of sampling (usually the wavelength) in meter. The default is 100e-6.
    freq0 : double, optional
        Sampling frequency. If defined, it dominates `lambda0`. The default is None.
        
    Returns
    -------
    wavelength : 1D array
        Wavelength of the signal transformed in frequency domain.
    spectrum : 1D or 2D array
        Spectra intensity of the signal transformed in frequency domain.

    '''
    
    if phase is not None:
        signal_comp = np.sqrt(inten)*(np.cos(phase)+np.sin(phase)*1j)
    else:
        if np.iscomplexobj(inten):
            signal_comp = inten
        else:
            print('The amp should be the complex fields if no phase is given!')
    
    nsample = len(signal_comp) # number of samples
    
    axis = 0
    spectrum = np.abs(np.fft.fftshift(np.fft.fft(signal_comp, nsample, axis), axis))
    spectrum = spectrum*spectrum
    
    if freq0 is None and lambda0 is not None:
        freq0 = 1./(lambda0/sample)*c0 # sampling frequency
    
    F = 1.0*np.arange(-nsample/2, nsample/2,)/nsample*freq0+freq0 # Frequency
    wavelength = c0/F # Frequency to wavelength
    
    return wavelength, spectrum



def nearest_index(a: np.ndarray, x, tie_break: str = "left"):
    """
    Return the index (or indices) of the element(s) in a sorted increasing array `a`
    that are nearest to the query value(s) `x`.

    Parameters
    ----------
    a : (N,) np.ndarray
        Strictly increasing 1D array (grid).
    x : float or array_like
        Query value(s).
    tie_break : {"left", "right"}, optional
        If a query falls exactly in the middle of two points, choose the
        left one ("left") or the right one ("right").

    Returns
    -------
    idx : int or np.ndarray of ints
        Index (or indices) of the nearest point(s).
    """
    a = np.asarray(a)
    x = np.asarray(x)

    # insertion positions
    i = np.searchsorted(a, x, side="left")

    # candidates on the left and right
    i_left  = np.clip(i - 1, 0, len(a) - 1)
    i_right = np.clip(i,     0, len(a) - 1)

    # distances to candidates
    d_left  = np.abs(x - a[i_left])
    d_right = np.abs(a[i_right] - x)

    # choose closer; handle ties by preference
    if tie_break == "left":
        pick_right = d_right < d_left
    elif tie_break == "right":
        pick_right = d_right <= d_left
    else:
        raise ValueError("tie_break must be 'left' or 'right'.")

    idx = np.where(pick_right, i_right, i_left)

    # Return a Python int for scalar input
    if idx.ndim == 0:
        return int(idx)
    return idx

def nearest_value(a: np.ndarray, x, tie_break: str = "left"):
    """
    Convenience wrapper returning the value(s) instead of index(es).
    """
    idx = nearest_index(a, x, tie_break=tie_break)
    return a[idx]





class MainResults(H5Proxy):
    mapping_v4 = dict(
        par_g_energy = '/Beam/Global/energy',
        par_g_energyspread = '/Beam/Global/energyspread',
        par_g_xposition = '/Beam/Global/xposition',
        par_g_xsize = '/Beam/Global/xsize',
        par_g_yposition = '/Beam/Global/yposition',
        par_g_ysize = '/Beam/Global/ysize',
        
        fld_g_energy = '/Field/Global/energy',
        fld_g_intnear = '/Field/Global/intensity-nearfield',
        fld_g_intfar = '/Field/Global/intensity-farfield',
        fld_g_xdivergence = '/Field/Global/xdivergence',
        fld_g_xpointing = '/Field/Global/xpointing',
        fld_g_xsize= '/Field/Global/xsize',
        fld_g_ydivergence = '/Field/Global/ydivergence',
        fld_g_ypointing = '/Field/Global/ypointing',
        fld_g_ysize= '/Field/Global/ysize',
        
        g_frequency = '/Global/frequency',
        g_gamma0 = '/Global/gamma0',
        g_lambdaref = '/Global/lambdaref',
        g_one4one = '/Global/one4one',
        g_s = '/Global/s',
        g_sample = '/Global/sample',
        g_scan = '/Global/scan',
        g_slen = '/Global/slen',
        g_time = '/Global/time',
        
        aw ='/Lattice/aw',
        ax ='/Lattice/ax',
        ay ='/Lattice/ay',
        chic_angle ='/Lattice/chic_angle',
        chic_lb ='/Lattice/chic_lb',
        chic_ld ='/Lattice/chic_ld',
        chic_lt ='/Lattice/chic_lt',
        cx ='/Lattice/cx',
        cy ='/Lattice/cy',
        dz ='/Lattice/dz',
        gradx ='/Lattice/gradx',
        grady ='/Lattice/grady',
        ku ='/Lattice/ku',
        kx ='/Lattice/kx',
        ky ='/Lattice/ky',
        phaseshift ='/Lattice/phaseshift',
        qf ='/Lattice/qf',
        qx ='/Lattice/qx',
        qy ='/Lattice/qy',
        slippage ='/Lattice/slippage',
        z ='/Lattice/z',
        zplot = '/Lattice/zplot',
        
        
        LSCfield = '/Beam/LSCfield',
        SSCfield = '/Beam/SSCfield',
        alphax = '/Beam/alphax',
        alphay = '/Beam/alphay',
        betax = '/Beam/betax',
        betay = '/Beam/betay',
        bunching = '/Beam/bunching',
        bunchingphase = '/Beam/bunchingphase',
        current = '/Beam/current',
        efield = '/Beam/efield',
        emax = '/Beam/emax',
        emin = '/Beam/emin',
        emitx = '/Beam/emitx',
        emity = '/Beam/emity',
        par_energy = '/Beam/par_energy',
        par_energyspread = '/Beam/par_energyspread',
        pxmax = '/Beam/pxmax',
        pxmin = '/Beam/pxmin',
        pxposition = '/Beam/pxposition',
        pymax = '/Beam/pymax',
        pymin = '/Beam/pymin',
        pyposition = '/Beam/pyposition',
        wakefield = '/Beam/wakefield',
        par_xmax = '/Beam/xmax',
        par_xmin = '/Beam/xmin',
        par_xposition = '/Beam/xposition',
        par_xsize = '/Beam/xsize',
        par_ymax = '/Beam/ymax',
        par_ymin = '/Beam/ymin',
        par_yposition = '/Beam/yposition',
        par_ysize = '/Beam/ysize',
        
        dgrid = '/Field/dgrid',
        gridspacing = '/Field/gridspacing',
        intnear = '/Field/intensity-nearfield',
        intfar = '/Field/intensity-farfield',
        ngrid = '/Field/ngrid',
        phinear = '/Field/phase-nearfield',
        phifar = '/Field/phase-farfield',
        power = '/Field/power',
        xdivergence = '/Field/xdivergence',
        xpointing = '/Field/xpointing',
        fld_xposition = '/Field/xposition',
        fld_xsize = '/Field/xsize',
        ydivergence = '/Field/ydivergence',
        ypointing = '/Field/ypointing',
        fld_yposition = '/Field/yposition',
        fld_ysize = '/Field/ysize',
        
        HOST = '/Meta/HOST',
        InputFile = '/Meta/InputFile',
        LatticeFile = '/Meta/LatticeFile',
        TimeStamp = '/Meta/TimeStamp',
        User = '/Meta/User',
        cwd = '/Meta/cwd',
        )
    cache: bool = True
    as_array: bool = True
    def __init__(self, fname: str | Path):
        fname = Path(fname)
        if not fname.name.endswith('out.h5'):
            raise ValueError('Genesis main output results filename must ends with \'out.h5\'')
        with h5py.File(fname, 'r') as hid:
            version_major = int(hid['Meta']['Version']['Major'][0])
            self.version = version_major
        if self.version == 4:
            mapping_loc = self.mapping_v4
        else:
            raise ValueError(f'Unsupported Genesis1.3 version {self.version}')
        super().__init__(h5_path=fname, mapping=mapping_loc, cache=self.cache, as_array=self.as_array)
        
    def get_spectrum(self, z=None, use_nearfield=False):
        if z is None:
            z = self.zplot[-1]
        lambda0 = self.g_lambdaref
        idx_zgrid = nearest_index(self.zplot, z)
        inten, phi = (self.intfar, self.phifar) if not use_nearfield else (self.intnear, self.phinear)
        return calcSpectrum_xk(inten[idx_zgrid, :], phi[idx_zgrid, :], lambda0=lambda0)
    
    def get_data_at_z(self, key:str, z: Union[float, str]='last') -> Tuple[np.ndarray, float]:
        # tmp_data = self.get(key)
        tmp_data = getattr(self, key)
        if tmp_data is None:
            raise KeyError(f'\'{key}\' --> None.')
        if tmp_data.shape[0] != len(self.zplot):
            raise ValueError('Please check data shape.')
        if z == 'last':
            idx = -1
        else:
            idx = nearest_index(self.zplot, z)
        z_new = self.zplot[idx]
        if len(tmp_data.shape) == 1:
            return tmp_data[idx], z_new
        else:
            return tmp_data[idx, :], z_new
    
    @property
    def wavelength_spectra_int(self):
        res = []
        lambda0 = self.g_lambdaref
        for idx in range(len(self.zplot)):
            res.append(calcSpectrum_xk(self.intfar[idx, :], self.phifar[idx, :], lambda0=lambda0)[1])
        res = np.vstack(res)
        return res
    
    @property
    def wavelength_spectra_wl(self):
        return calcSpectrum_xk(self.intfar[0, :], self.phifar[0, :], lambda0=self.g_lambdaref)[0]
    
    
    
    @property
    def t_from_s(self):
        return -self.g_s/c0
    
    @property
    def lslice(self):
        return self.g_lambdaref * self.g_sample
    
    @property
    def nslice(self):
        return len(self.g_frequency)
    
    @property
    def slice_num(self):
        return np.arange(self.nslice)+1
    
    @property
    def file_basename(self):
        return os.path.basename(self.h5_path)
    
    @property
    def seed_label(self):
        return self.file_basename.split('.')[1]
    
    @property
    def nslice_eff(self):
        astra2slices_log_fname = 'ast2g4slices.'+  self.seed_label + '.log'
        try:
            return max_slice_index(os.path.join(self.cwd, astra2slices_log_fname))+1
        except:
            return self.nslice-100
    
    @property
    def zpower(self):
        return np.sum(self.power, axis=1)
    
    @property
    def peakpower(self):
        return np.max(self.power, axis=1)
    
    @property
    def zenergy(self):
        if 'Global' in self._f['Field']:
            return self.fld_g_energy
        else:
            return self.zpower*self.lslice/c0
        
    @property
    def zsigmat_fld(self):
        t = self.g_s/c0
        res = []
        for iz in range(len(self.zplot)):
            i1d = Intensity1D(x=t, I=self.intfar[iz, :])
            sigmat = i1d.rms_width()['sigma'] if not all(i1d.I==0) else 0.
            res.append(sigmat)
        if self.as_array:
            return np.asarray(res)
        else:
            return res
        
    @property
    def zfwhm_fld(self):
        t = self.g_s/c0
        res = []
        for iz in range(len(self.zplot)):
            i1d = Intensity1D(x=t, I=self.intfar[iz, :])
            fwhm = i1d.fwhm()['width'] if not all(i1d.I==0) else 0.
            res.append(fwhm)
        if self.as_array:
            return np.asarray(res)
        else:
            return res
        
    @property
    def mpisize(self):
        return int(self._f['/Meta/mpisize'][0])
    
    def attr2colregistry_name(self, key:str) -> str:
        if key in self.mapping.keys():
            return self.mapping[key].split('/')[-1]
        else:
            match key:
                case 't_from_s'|'zsigmat_fld'|'zfwhm_fld':
                    return 'time'
                case 'zpower':
                    return 'power'
                case 'zenergy':
                    return 'energy'
                case _:
                    if hasattr(self, key):
                        return key
                    else:
                        raise KeyError(f'MainResults has no attribute \'{key}\'')
                        
    @property
    def colregistry_names(self):
        names = set()
        for key in self.mapping.keys():
            # names.add(self.attr2colregistry_name(key))
            names.add(key)
        for key in dir(self):
            if not key.startswith('__') and not key.startswith('_') and \
                not key in [
                    'as_array',
                    'attr2colregistry_name',
                    'cache',
                    'clear_cache',
                    'close',
                    'file_basename',
                    'get',
                    'get_data_at_z',
                    'get_spectrum',
                    'h5_path',
                    'mapping',
                    'mapping_v4',
                    'print_structure',
                    'version',
                    'colregistry_names',
                    ]:
                # names.add(self.attr2colregistry_name(key))
                names.add(key)
        return names

class FieldResults(H5Proxy):
    mapping_v4 = dict(
        gridpoints = '/gridpoints',
        gridsize = '/gridsize',
        int_xy = '/int_xy',
        int_xz = '/int_xz',
        int_yz = '/int_yz',
        refposition = '/refposition',
        slicecount = '/slicecount',
        slicespacing = 'slicespacing',
        wavelength = '/wavelength',
        )
    cache: bool = True
    as_array: bool = True
    
    def __init__(self, fname: str):
        if not fname.endswith('fld.h5'):
            raise ValueError('Genesis field dump results filename must ends with \'fld.h5\'')
        with h5py.File(fname, 'r') as hid:
            version_major = int(hid['Meta']['Version']['Major'][0])
            self.version = version_major
        if self.version == 4:
            mapping_loc = self.mapping_v4
        else:
            raise ValueError(f'Unsupported Genesis1.3 version {self.version}')
        super().__init__(h5_path=fname, mapping=mapping_loc, cache=self.cache, as_array=self.as_array)
        
    def get_slice_int_xy(self, slice_no: int, reshape_array=True, return_real_imag=False):
        if slice_no < 1 or slice_no > self.slicecount:
            raise ValueError(f'{slice_no} exceeds boundary: 1 to self.slicecount')
        slice_key = 'slice' + f'{slice_no:0>6}'
        path_real = '/'+slice_key+'/field-real'
        path_imag = '/'+slice_key+'/field-imag'
        if not self.as_array:
            return self._get_obj(path_real), self._get_obj(path_imag)
        
        data_real = self._read_dataset(path_real)
        data_real = self._maybe_decode_strings(data_real)
        
        data_imag = self._read_dataset(path_imag)
        data_imag = self._maybe_decode_strings(data_imag)
        
        if reshape_array:
            data_real = data_real.reshape([self.gridpoints, self.gridpoints], order='F') #order 'F' or 'C'?
            data_imag = data_imag.reshape([self.gridpoints, self.gridpoints], order='F') #order 'F' or 'C'?
        
        if return_real_imag:
            return data_real, data_imag
        
        data_comp = data_real + 1j*data_imag
        inten = np.abs(data_comp) ** 2
        phase = np.angle(data_comp)
        
        return inten, phase
    
    def get_prj_int_xy(self, reshape_array=True):
        return np.asarray(self.int_xy).reshape([self.gridpoints, self.gridpoints], order='F') #order 'F' or 'C'?
    
    def get_int_onaxis(self):
        data = []
        idx_axis = self.gridpoints//2
        for idx in range(self.slicecount):
            int_onaixs_slice = self.get_slice_int_xy(idx+1, reshape_array=True, return_real_imag=False)[0][idx_axis, idx_axis]
            data.append(int_onaixs_slice)
        if self.as_array:
            data = np.asarray(data)
        return data
    
    def _get_int_onaxis_db(self):
        data = []
        idx_axis = self.gridpoints*self.gridpoints//2
        for idx in range(self.slicecount):
            int_onaixs_slice = self.get_slice_int_xy(idx+1, reshape_array=False, return_real_imag=False)[0][idx_axis]
            data.append(int_onaixs_slice)
        if self.as_array:
            data = np.asarray(data)
        return data

    @property
    def xgrids(self):
        width_range = self.gridsize * (self.gridpoints - 1)
        xgrids = np.linspace(-width_range/2, width_range/2, self.gridpoints)
        return xgrids
    
    @property
    def ygrids(self):
        return self.xgrids
    
    @property
    def zgrids(self):
        slicespacing = self.slicespacing
        slicecount = self.slicecount
        return np.arange(0, slicespacing*slicecount, slicespacing) + slicespacing/2

class ParticleResults(H5Proxy):
    mapping_v4 = dict(
        beamletsize = '/beamletsize',
        one4one = '/one4one',
        refposition = '/refposition',
        slicecount = '/slicecount',
        slicelength = '/slicelength',
        slicespacing = '/slicespacing',
        )
    cache: bool = True
    as_array: bool = True
    
    def __init__(self, fname: str):
        if not fname.endswith('par.h5'):
            raise ValueError('Genesis particles dump results filename must ends with \'par.h5\'')
        with h5py.File(fname, 'r') as hid:
            version_major = int(hid['Meta']['Version']['Major'][0])
            self.version = version_major
        if self.version == 4:
            mapping_loc = self.mapping_v4
        else:
            raise ValueError(f'Unsupported Genesis1.3 version {self.version}')
        super().__init__(h5_path=fname, mapping=mapping_loc, cache=self.cache, as_array=self.as_array)

    # ----------------- internal helpers -----------------

    def _list_slice_groups(self) -> List[Tuple[int, str]]:
        """
        Return a sorted list of (slice_index, group_name) for groups named
        'sliceXXXXXX' at the root level.
        """
        result: List[Tuple[int, str]] = []
        for name in self._f.keys():
            if not name.startswith("slice"):
                continue
            suffix = name[5:]
            if len(suffix) == 6 and suffix.isdigit():
                idx = int(suffix)
                result.append((idx, name))
        result.sort(key=lambda x: x[0])
        return result

    @staticmethod
    def _theta_to_z(theta: np.ndarray, lambda_r: float) -> np.ndarray:
        """
        Convert theta (phase) to longitudinal position z using:
            z = theta / (2*pi) * lambda_r
        """
        theta = np.asarray(theta, dtype=float)
        return theta / (2.0 * np.pi) * float(lambda_r)

    def _compute_particle_charge(
        self, current: float, n_particles: int
    ) -> float:
        """
        Compute per-particle charge [C] from slice current and slice length.

        Assumes:
          - current [A]
          - slicelength [m]
          - v ~ c

        Then:
          Q_slice = current * (slicelength / c)
          q_particle = Q_slice / n_particles
        """
        if n_particles <= 0:
            raise ValueError("n_particles must be > 0.")

        # slicelength may be stored as a small dataset; use the first element
        slice_length_arr = np.asarray(self.slicelength, dtype=float)
        slice_length = float(slice_length_arr.reshape(-1)[0])

        q_slice = current * (slice_length / c0)
        return q_slice / float(n_particles)

    # ----------------- public APIs -----------------

    def get_slice_particles(
        self, slice_index: int, *, lambda_r: Optional[float] = None
    ) -> np.ndarray:
        """
        Get the particle distribution matrix for a single slice.
        
        The returned array has shape (N, 8) with columns:
            (x, y, z, px, py, pz, q, sliceid)
        
        Here:
            - x, y     : transverse positions of particles in the slice.
            - z        : absolute longitudinal position of particles.
                         It is computed as:
                             z_within = theta / (2*pi) * lambda_r
                             z_center = (slice_index - 0.5) * slicespacing[0]
                         and then:
                             z = z_center + z_within
            - px, py, pz : momentum components (pz obtained from gamma, px, py).
            - q        : per-particle charge [C], computed from the slice
                         current and slicelength[0] assuming v ≈ c.
            - sliceid  : slice index stored as a float, identical for all
                         particles in the same slice.
        
        Parameters
        ----------
        slice_index : int
            Integer index of the slice, as in 'sliceXXXXXX'.
        lambda_r : float, optional (keyword-only)
            Effective wavelength [m] used for converting theta to z:
                z_within = theta / (2*pi) * lambda_r
            If None (default), lambda_r is taken as self.slicelength.
        
        Returns
        -------
        particles : np.ndarray
            Array of shape (N, 8) containing the particle phase-space data
            for the specified slice.
        """

        # Resolve group name
        group_name = f"slice{slice_index:06d}"
        if group_name not in self._f:
            raise KeyError(f"Slice group '{group_name}' not found in file.")

        grp = self._f[group_name]

        # Read datasets
        current_ds = grp["current"][()]  # scalar
        current = float(np.asarray(current_ds).reshape(()))

        x = np.asarray(grp["x"][()], dtype=float)
        y = np.asarray(grp["y"][()], dtype=float)
        gamma = np.asarray(grp["gamma"][()], dtype=float)
        px = np.asarray(grp["px"][()], dtype=float)
        py = np.asarray(grp["py"][()], dtype=float)
        theta = np.asarray(grp["theta"][()], dtype=float)

        # Consistency check
        n = x.shape[0]
        for arr, name in [(y, "y"), (gamma, "gamma"), (px, "px"), (py, "py"), (theta, "theta")]:
            if arr.shape[0] != n:
                raise ValueError(
                    f"Inconsistent array length in slice {slice_index}: "
                    f"x has {n}, but {name} has {arr.shape[0]}."
                )

        if n == 0:
            # Return empty (0, 8) array if there are no particles
            return np.empty((0, 8), dtype=float)

        # Default lambda_r: use self.slicelength
        if lambda_r is None:
            lambda_r = self.slicelength

        # z from theta (within-slice coordinate)
        z = self._theta_to_z(theta, lambda_r=lambda_r)
        
        # Compute slice center position:
        # slice000001 -> idx=1 -> center = spacing * (1 - 0.5) = spacing/2
        z_center = (float(slice_index) - 0.5) * self.slicespacing
        
        # Shift z column by slice center
        z += z_center

        # pz from gamma, px, py: p^2 = gamma^2 - 1, pz^2 = p^2 - px^2 - py^2
        p2 = gamma**2 - 1.0
        p_perp2 = px**2 + py**2
        pz2 = np.maximum(p2 - p_perp2, 0.0)
        pz = np.sqrt(pz2)

        # Particle charge q
        q_particle = self._compute_particle_charge(current=current, n_particles=n)
        q = np.full(n, q_particle, dtype=float)

        # Slice id column (same for all particles)
        sliceid = np.full(n, float(slice_index), dtype=float)

        # Stack columns: (x, y, z, px, py, pz, q, sliceid)
        particles = np.column_stack([x, y, z, px, py, pz, q, sliceid])
        return particles

    def get_all_particles(
        self,
        exclude_zero_current: bool = True,
        lambda_r: Optional[float] = None,
        zero_tol: float = 0.0,
    ) -> np.ndarray:
        """
        Get the particle distribution matrix for all slices in the file.
        
        For each slice, this method internally calls `get_slice_particles`,
        so the z coordinate is already the absolute longitudinal position:
            z_total = z_center(slice_index) + z_within_slice
        where z_center is determined from self.slicespacing and the
        slice index:
            center(slice000001) = slicespacing[0] / 2
            center(slice_index) = (slice_index - 0.5) * slicespacing[0]
        
        Slices can optionally be filtered by their current value.
        
        Parameters
        ----------
        exclude_zero_current : bool, optional
            If True (default), slices with |current| <= zero_tol are skipped.
        lambda_r : float, optional
            Effective wavelength [m] used for converting theta to z in
            `get_slice_particles`. If None (default), lambda_r is taken
            as self.slicelength.
        zero_tol : float, optional
            Tolerance for considering a slice "zero-current". A slice is
            treated as zero-current if |current| <= zero_tol. Default is 0.0.
        
        Returns
        -------
        particles : np.ndarray
            Concatenated particle matrix of shape (N_total, 8), where N_total
            is the total number of particles in all included slices.
            If no slices are selected, returns an empty array with shape (0, 8).
        """

        all_slices = self._list_slice_groups()
        chunks: list[np.ndarray] = []

        # Slice spacing: use the first element of slicespacing dataset
        # spacing = self.slicespacing

        for idx, name in all_slices:
            grp = self._f[name]
            current_ds = grp["current"][()]
            current = float(np.asarray(current_ds).reshape(()))

            if exclude_zero_current and abs(current) <= zero_tol:
                continue

            # Get within-slice particle distribution
            slice_particles = self.get_slice_particles(
                slice_index=idx, lambda_r=lambda_r
            )

            if slice_particles.size == 0:
                continue

            chunks.append(slice_particles)

        if not chunks:
            return np.empty((0, 8), dtype=float)

        return np.vstack(chunks)

    def current(self):
        all_slices = self._list_slice_groups()
        current_path = [f'/{sl[1]}/current' for sl in all_slices]
        cur = np.asarray([self._f[p][0] for p in current_path], dtype=float)
        return cur
    
    def recompute_current(
        self,
        bins: Optional[Union[int, np.ndarray]] = None,
        *,
        exclude_zero_current: bool = True,
        lambda_r: Optional[float] = None,
        zero_tol: float = 0.0,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Recompute the longitudinal current profile from the particle distribution.

        This method:
          1) Calls `get_all_particles(...)` to obtain the full particle set with
             columns (x, y, z, px, py, pz, q, sliceid).
          2) Uses a 1D histogram over z with weights = q to accumulate the
             charge per bin: Q_bin = sum_i q_i.
          3) Converts charge in each bin into an average current:
                 I_bin = Q_bin * c0 / Δz_bin,
             where Δz_bin is the bin width and c0 is the speed of light.

        By default, the bin edges are chosen to be consistent with the original
        Genesis slices:
            - Let N be the number of slice groups.
            - Let spacing = self.slicespacing.
            - Slice centers are at:
                  z_center(idx) = (idx - 0.5) * spacing,  idx = 1..N
            - Default bin edges are:
                  z_edges = [0, spacing, 2*spacing, ..., N*spacing],
              i.e. each bin spans the region between two neighboring slice
              centers, and the first/last edges are at 0 and N*spacing.

        You may override this behavior by providing a custom `bins` argument,
        which is passed directly to `numpy.histogram`:
            - If `bins` is an integer, it is the number of bins.
            - If `bins` is a 1D array, it is interpreted as explicit bin edges.

        Parameters
        ----------
        bins : int or array-like, optional
            Bin specification, passed to `numpy.histogram`. If None (default),
            bin edges aligned with the original slice spacing are used:
                z_edges = np.linspace(0, N*spacing, N+1).
        exclude_zero_current : bool, optional
            Forwarded to `get_all_particles`. If True (default), slices with
            |current| <= zero_tol are skipped when constructing the particle set.
        lambda_r : float, optional
            Forwarded to `get_all_particles` (and then to `get_slice_particles`)
            as the effective wavelength [m] used to convert theta to z.
            If None (default), lambda_r is taken as self.slicelength.
        zero_tol : float, optional
            Tolerance for considering a slice "zero-current" in
            `get_all_particles`. A slice is treated as zero-current if
            |current| <= zero_tol. Default is 0.0.

        Returns
        -------
        z_centers : np.ndarray
            1D array of bin-center positions [m], shape (Nbins,).
        I : np.ndarray
            1D array of average current values [A] in each bin, shape (Nbins,).
        """
        # Get all particles (possibly excluding zero-current slices)
        particles = self.get_all_particles(
            exclude_zero_current=exclude_zero_current,
            lambda_r=lambda_r,
            zero_tol=zero_tol,
        )

        # No particles at all -> return empty arrays
        if particles.size == 0:
            return np.empty((0,), dtype=float), np.empty((0,), dtype=float)

        z = particles[:, 2]  # longitudinal position
        q = particles[:, 6]  # charge per particle [C]

        # Default bins: aligned with original slice spacing
        if bins is None:
            all_slices = self._list_slice_groups()
            N = len(all_slices)
            if N == 0:
                return np.empty((0,), dtype=float), np.empty((0,), dtype=float)

            spacing = float(np.asarray(self.slicespacing, dtype=float).reshape(-1)[0])
            z_edges = np.linspace(0.0, N * spacing, N + 1)
        else:
            # Let numpy.histogram handle both integer and array-like bins
            z_edges = bins

        # Histogram of charge along z
        Q_hist, edges = np.histogram(z, bins=z_edges, weights=q)

        # Bin widths Δz
        dz = edges[1:] - edges[:-1]
        # Avoid division by zero (just in case)
        dz_safe = np.where(dz == 0, np.nan, dz)

        # Convert charge per bin to average current: I = Q * c0 / Δz
        I = Q_hist * c0 / dz_safe

        # Bin centers for plotting / analysis
        z_centers = 0.5 * (edges[1:] + edges[:-1])

        return z_centers, I
    
    def recompute_bunching_factor(
        self,
        *,
        harmonic: int = 1,
        exclude_zero_current: bool = True,
        lambda_r: Optional[float] = None,
        zero_tol: float = 0.0,
        return_complex: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute the bunching factor as a function of longitudinal position z.
    
        Electrons are first regrouped into longitudinal slices using the same
        z-binning convention as `recompute_current`, i.e. bins aligned with
        the original Genesis slice spacing. The bin edges are NOT configurable
        here by design:
    
            - Let N be the number of slice groups in the file.
            - Let spacing = self.slicespacing.
            - Bin edges are:
                  z_edges = [0, spacing, 2*spacing, ..., N*spacing]
            - Bin centers are:
                  z_centers[j] = (j + 0.5) * spacing,  j = 0..N-1
    
        For each bin j, the (complex) bunching factor at a given harmonic h is
        computed as a charge-weighted phase average:
    
            k_h     = 2*pi*h / lambda_r
            theta_j = k_h * (z_j - z_centers[j])
            b_j     = (1 / sum_i q_i) * sum_i q_i * exp(1j * theta_i)
    
        where:
            - z_j, q_j are the longitudinal position and charge of each
              particle in that bin;
            - lambda_r is the wavelength used to define the phase;
            - h is the harmonic number.
    
        Parameters
        ----------
        harmonic : int, optional
            Harmonic number h in the phase factor exp(i * h * k * z).
            Default is 1 (fundamental).
        exclude_zero_current : bool, optional
            Forwarded to `get_all_particles`. If True (default), slices with
            |current| <= zero_tol are skipped when constructing the particle set.
        lambda_r : float, optional
            Effective wavelength [m] used to define the phase. If None
            (default), lambda_r is taken as self.slicelength, consistent
            with `get_slice_particles` and `get_all_particles`.
        zero_tol : float, optional
            Tolerance for considering a slice "zero-current" in
            `get_all_particles`. A slice is treated as zero-current if
            |current| <= zero_tol. Default is 0.0.
        return_complex : bool, optional
            If False (default), the returned bunching factor array is the
            magnitude |b_j|. If True, the full complex bunching factor b_j
            is returned.
    
        Returns
        -------
        z_centers : np.ndarray
            1D array of bin-center positions [m], shape (Nbins,).
        b : np.ndarray
            1D array of bunching factors for each bin, shape (Nbins,).
            - If return_complex=False: real array with |b_j|.
            - If return_complex=True: complex array with b_j.
        """
        # Get all particles (possibly excluding zero-current slices)
        particles = self.get_all_particles(
            exclude_zero_current=exclude_zero_current,
            lambda_r=lambda_r,
            zero_tol=zero_tol,
        )
    
        # No particles at all -> return empty arrays
        if particles.size == 0:
            return np.empty((0,), dtype=float), np.empty((0,), dtype=complex if return_complex else float)
    
        z = particles[:, 2]  # longitudinal position
        q = particles[:, 6]  # charge per particle [C]
    
        # Determine lambda_r (consistent default)
        if lambda_r is None:
            lambda_r_arr = np.asarray(self.slicelength, dtype=float)
            lambda_r = float(lambda_r_arr.reshape(-1)[0])
        else:
            lambda_r = float(lambda_r)
    
        # Build fixed bin edges aligned with original slice spacing
        all_slices = self._list_slice_groups()
        N = len(all_slices)
        if N == 0:
            return np.empty((0,), dtype=float), np.empty((0,), dtype=complex if return_complex else float)
    
        spacing_arr = np.asarray(self.slicespacing, dtype=float)
        spacing = float(spacing_arr.reshape(-1)[0])
    
        z_edges = np.linspace(0.0, N * spacing, N + 1)
        z_centers = 0.5 * (z_edges[1:] + z_edges[:-1])
    
        # Wave number for the given harmonic
        k_h = 2.0 * np.pi * float(harmonic) / lambda_r
    
        # Allocate complex bunching factor
        b_complex = np.zeros(N, dtype=complex)
    
        # Loop over bins and compute charge-weighted phase average
        for j in range(N):
            if j < N - 1:
                mask = (z >= z_edges[j]) & (z < z_edges[j + 1])
            else:
                # Include the rightmost edge in the last bin
                mask = (z >= z_edges[j]) & (z <= z_edges[j + 1])
    
            if not np.any(mask):
                continue
    
            z_bin = z[mask]
            q_bin = q[mask]
    
            q_sum = np.sum(q_bin)
            if q_sum == 0.0:
                continue
    
            # Phase relative to the bin center
            theta_bin = k_h * (z_bin - z_centers[j])
            b_complex[j] = np.sum(q_bin * np.exp(1j * theta_bin)) / q_sum
    
        if return_complex:
            return z_centers, b_complex
        else:
            return z_centers, np.abs(b_complex)
