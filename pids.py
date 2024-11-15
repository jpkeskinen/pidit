# Luokka PIDS-tiedostoja varten

# 2024
# Jukka-Pekka Keskinen

import xarray as xr
import rioxarray as rxr
from datetime import datetime, timezone
import yaml
import sys
import numpy as np


class Pids:
    def __init__(self):
        self.xrds = xr.Dataset()
        self.xrds.attrs['Conventions'] = 'CF-1.7'
        self.xrds.attrs['origin_lon'] = 25.74741
        self.xrds.attrs['origin_lat'] = 62.24264
        self.xrds.attrs['origin_time'] = str(
            datetime.now(timezone.utc).replace(microsecond=0))[:-6] + ' +00'
        self.xrds.attrs['origin_x'] = 434918.0
        self.xrds.attrs['origin_y'] = 6901840.0
        self.xrds.attrs['origin_z'] = 0.0
        self.xrds.attrs['rotation_angle'] = 0.0
        

    def luku_tiedostosta(self, polku):
        with open(polku, 'r') as f:
            data = yaml.safe_load(f)

        # Globaalit attribuutit
        # Tekstimuotoiset
        for i in ['origin_time', 'acronym', 'author', 'campaign',
                  'contact_person', 'comment', 'data_content',
                  'dependencies', 'keywords', 'license', 'location',
                  'site', 'source', 'title']:
            if i in data:
                self.xrds.attrs[i] = str(data[i])

        # Liukuluvut    
        for i in ['origin_lon', 'origin_lat', 'origin_x', 'origin_y',
                  'origin_z', 'rotation_angle', 'palm_version']:
            if i in data:
                self.xrds.attrs[i] = float(data[i])

        # Kokonaisluvut
        if 'version' in data:
            self.xrds.attrs['version'] = int(data['version'])

        # CRS
        if 'crs' in data:
            CRS = xr.DataArray(7)

            # Koordinaattijärjestelmän atribuutit
            # Tekstimuotoiset
            for i in ['grid_mapping_name', 'units', 'epsg_code']:
                if i in data['crs']:
                    CRS.attrs[i] = str(data['crs'][i])
                else:
                    sys.exit('CRS-tiedoista puuttuu '+i)                                

            # Liukulukumuotoiset
            for i in ['semi_major_axis', 'inverse_flattening',
                      'longitude_of_prime_meridian',
                      'longitude_of_central_meridian',
                      'latitude_of_projection_origin',
                      'scale_factor_at_central_meridian',
                      'false_easting', 'false_northing']:
                if i in data['crs']:
                    CRS.attrs[i] = float(data['crs'][i])
                else:
                    sys.exit('CRS-tiedoista puuttuu '+i)                                

            self.xrds['crs'] = CRS

        # Luetaan maanpintatiedot
        if 'dem' in data:
            D = rxr.open_rasterio(data['dem'])
            D = D.isel(band=0).sortby('y')
            if not 'x' in self.xrds.coords and not 'y' in self.xrds.coords:
                self.luo_xy((D.x-D.x[0]).data.astype(np.float32),
                            (D.y-D.y[0]).data.astype(np.float32))

            self.xrds['zt'] = (('x', 'y'), D.data)
            self.xrds['zt'].attrs['units'] = 'm'
            self.xrds['zt'].attrs['long_name'] = 'terrain height'
            self.xrds['zt'].attrs['_FillValue'] = -9999.0

            D.close()
            del D

        # Luetaan latvustotiedot. Siirtymä 2D-rasterista 3D:hen
        # tapahtuu samoin kuin P4UL:ssa.
        if 'chm' in data:
            if 'tiedosto' in data['chm']:
                R = rxr.open_rasterio(data['chm']['tiedosto'])
                dx = np.abs([R.x[2].data-R.x[1].data, R.y[2].data-R.y[1].data])
                if 'dz' in data['chm']:
                    dz = float(data['chm']['dz'])
                else:
                    dz = dx[0]
                D = _chm_p4ul(R.isel(band=0).sortby('y').data,dx,dz=dz)

                if 'x' in self.xrds.coords and 'y' in self.xrds.coords:
                    if not self.xrds.x.size == R.x.size or self.xrds.y.size == R.y.size:
                        sys.exit('Koordinaatistot eivät täsmää.')
                else:
                    self.luo_xy((R.x-R.x[0]).data.astype(np.float32),
                            (R.y-R.y[0]).data.astype(np.float32))

                self.xrds['zlad'] = dz*(np.arange(D.shape[-1])).astype(np.float32)                
                
                self.xrds['lad'] = (('x', 'y', 'zlad'), D)

                R.close()
                del R
                del D
                                        
            elif 'tiedosto3d' in data['chm']:
                print('Luodaan latvustotiedot 3D-tiedostosta.')
                D = rxr.open_rasterio(data['chm']['tiedosto3d']).sortby('y')

                # Oletetaan, että luettavassa tiedostossa ensimmäine  taso on 0 m.
                if 'dztiff' in data['chm']:
                    dz0 = float(data['chm']['dztiff'])
                elif 'dz' in data['chm']:
                    dz0 = float(data['chm']['dz'])
                else:
                    dz0 = 1.0
            
                if 'x' in self.xrds.coords and 'y' in self.xrds.coords:
                    if not self.xrds.x.size == D.x.size and not self.xrds.y.size == D.y.size:
                        sys.exit('Koordinaatistot eivät täsmää.')
                else:
                    self.luo_xy((D.x-D.x[0]).data.astype(np.float32),
                                (D.y-D.y[0]).data.astype(np.float32))

                self.xrds['zlad'] = dz0*(D.band.data-1).astype(np.float32)

                self.xrds['lad'] = (('zlad', 'y', 'x'), D.data)

                D.close()
                del D

            else:
                sys.exit('Puuttuva tiedosto chm-tiedoissa.')


            # Muokataan z-akseli kuntoon.
            if 'dz' in data['chm']:
                dz = float(data['chm']['dz'])
            else:
                dz = dz0
                
            if 'interpolointi' in data['chm']:
                inmen = data['chm']['interpolointi']
            else:
                inmen = 'nearest'
                
            zu = np.append(0.0, np.arange(dz/2, self.xrds['zlad'][-1]+dz/100, dz, dtype=np.float32) )
            self.xrds['lad'] = self.xrds['lad'].interp(zlad=zu, method=inmen)
            
            self.xrds['lad'].attrs['units'] = 'm2 m-3'
            self.xrds['lad'].attrs['long_name'] = 'leaf area density'
            self.xrds['lad'].attrs['_FillValue'] = -9999.0
            self.xrds['zlad'].attrs['units'] = 'm'
            self.xrds['zlad'].attrs['long_name'] = 'height above ground'
            self.xrds['zlad'].attrs['positive'] = 'up'
            self.xrds['zlad'].attrs['axis'] = 'Z'
    
            
    def tallennus(self, polku='PIDS_STATIC'):
        self.xrds.attrs['history'] = str(datetime.now().replace(microsecond=0)) + ': File created'
        self.xrds.attrs['creation_time'] = str(
            datetime.now(timezone.utc).replace(microsecond=0))[:-6] + ' +00'
        self.xrds.to_netcdf(polku)

    def luo_xy(self, x, y):
        """Luodaan x- ja y-koordinaatit tif-tiedoston perusteella.

        Argumentit:
        tiedosto: str, tiedoston nimi.
        """
        if 'x' not in self.xrds.coords and not 'y' in self.xrds.coords:
            self.xrds['x'] = x
            self.xrds['x'].attrs['units'] = 'm'
            self.xrds['x'].attrs['long_name'] = 'distance to origin in x-direction'
            self.xrds['x'].attrs['axis'] = 'X'
            self.xrds['y'] = y
            self.xrds['y'].attrs['units'] = 'm'
            self.xrds['y'].attrs['long_name'] = 'distance to origin in y-direction'
            self.xrds['y'].attrs['axis'] = 'Y'

        
def _chm_p4ul(R, dPx, laiRef=6.0, zref=[4.0, 20.0], dz=None):
    # The function code is adapted from P4UL
    # The code is licensed under the MIT License.
    # Copyright (c) 2017 Mikko J.S. Auvinen
    
    nPx = np.shape(R)

    # Calculate the shape of the new 3D array, use largest in-canopy value
    nPx3D = nPx; dPx3D = dPx
    if ( dz ):
        dPx3D = np.append(dPx, dz)
    else:
        dPx3D = np.append(dPx, dPx[0])

    nPx3D = np.append(nPx3D, int(np.floor(np.amax(R)/dPx3D[2])+1))

    # Fill the 3D canopy array
    canopy = np.zeros([nPx3D[1], nPx3D[0], nPx3D[2]])
    nPc=[nPx3D[1], nPx3D[0], nPx3D[2]]
    dPc=[dPx3D[1], dPx3D[0], dPx3D[2]]
    print(" 3D grid array dimensions [x,y,z]: {}, {}, {}".format(*nPc))
    print(" Generating vertical distributions of leaf area densities ...")


    # Compute <LAD>_z and starting index of the foliage using reference values
    lad_const = laiRef/(zref[1]-zref[0])
    k1        = int( np.round(zref[0]/float(dPc[2])) )  # starting k index

    print(' Rry shape = {} '.format(R.shape))

    # Calculate leaf area density profiles for each horizontal grid tile and fill array vertically
    for j in range(nPc[1]):
        for i in range(nPc[0]):
            Zi = R[j,i] # Zi := canopy height at [j,i]
            # Check if there is canopy at all in the vertical column
            if (Zi <= zref[0]):
                continue

            # Number of layers
            dZ   = Zi - zref[0]
            nind = int(np.floor( dZ/float(dPc[2]) )) + 1

            k2 = int(np.ceil(Zi/dPc[2]))+1
            k2 = min( k2, nPc[2] )
            canopy[i,j,k1:k2] = lad_const

    return canopy
