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

            CRS.attrs['long_name'] = 'coordinate reference system'
            self.xrds['crs'] = CRS

        # Luetaan sijaintitiedot jos niitä ei ole annettu eksplisiittisesti
        if ('origin_lon' not in data or 'origin_lat' not in data
            or 'origin_x' not in data or 'origin_y' not in data):
            if 'dem' in data:
                print('Alueen sijaintitiedot otetaan DEM-tiedostosta.')
                D = rxr.open_rasterio(data['dem'])
            elif 'chm' in data:
                print('Alueen sijaintitiedot otetaan CHM-tiedostosta.')
                if 'tiedosto' in data['chm']:
                    D = rxr.open_rasterio(data['chm']['tiedosto'])
                elif 'tiedosto3d' in data['chm']:
                    D = rxr.open_rasterio(data['chm']['tiedosto3d'])
                else:
                    print('CHM-tiedostoa ei ole määritelty.')
            else:
                print('Sijaintitiedot puuttuvat.')


            blonlat = D.rio.transform_bounds("EPSG:4326")
            bxy = D.rio.bounds()
            self.xrds.attrs['origin_lon'] = float(blonlat[0])
            self.xrds.attrs['origin_lat'] = float(blonlat[1])
            self.xrds.attrs['origin_x'] = float(bxy[0])
            self.xrds.attrs['origin_y'] = float(bxy[1])
            D.close()
            del D

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
                self.luo_lad_2dchm(data['chm']['tiedosto'],dz=data['chm']['dz'])
            elif 'tiedosto3d' in data['chm']:
                if 'dz' in data['chm']:
                    dz = data['chm']['dz']
                else:
                    dz = None
                self.luo_lad_3dchm(data['chm']['tiedosto3d'],dz=dz)
            else:
                sys.exit('Puuttuva tiedosto chm-tiedoissa.')

            # Attribuutit
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

    def luo_lad_2dchm(self,tnimi,dz=None):
        """Luodaan latvustutiedot 2D-tiedostosta."""
        # 2D-tapauksessa zlad-akseli on sama kuin 3D-tiedon
        # luonnissa käytetty. Se menee siis kerralla oikein.
        R = rxr.open_rasterio(tnimi)
        dx = np.abs([R.x[2].data-R.x[1].data, R.y[2].data-R.y[1].data])
        if dz is None:
            dz = dx[0]
        else:
            dz = float(dz)
            
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

    def luo_lad_3dchm(self, tnimi,dz=None,inmen='nearest'):
        """Luodaan latvustotiedot 3D-tiedostosta."""
        # 3D-tapauksessa zlad-akseli pitää mahdollisesti vielä
        # vaihtaa.
        print('Luodaan latvustotiedot 3D-tiedostosta.')
        D = rxr.open_rasterio(tnimi).sortby('y')

        if dz==None:
            if 'dz' in D.rio.attrs:
                dz = float(D.rio.attrs['dz'])
            else:
                print('dz-tietoa ei ole annettu, käytetään oletusarvoa 1.0 m.')
                dz = 1.0
        
        # Oletetaan, että luettavassa tiedostossa ensimmäine  taso on 0 m.
        if 'x' in self.xrds.coords and 'y' in self.xrds.coords:
            if not self.xrds.x.size == D.x.size and not self.xrds.y.size == D.y.size:
                sys.exit('Koordinaatistot eivät täsmää.')
        else:
            self.luo_xy((D.x-D.x[0]).data.astype(np.float32),
                        (D.y-D.y[0]).data.astype(np.float32))

        DD = xr.DataArray(D.data, dims=['zlad', 'y', 'x'],
                          coords={'zlad': dz*(D.band.data-1).astype(np.float32),
                                  'y': (D.y-D.y[0]).data.astype(np.float32),
                                  'x': (D.x-D.x[0]).data.astype(np.float32)})
                    

        # Muokataan z-akseli kuntoon.
        zu = np.append(0.0, np.arange(dz/2, DD['zlad'][-1]+dz/100, dz, dtype=np.float32) )

        self.xrds['lad'] = DD.interp(zlad=zu, method=inmen)

        D.close()

def _chm_p4ul(R, dPx, laiRef=6.0, zref=[4.0, 20.0], dz=None):
    # The code of this function is adapted from P4UL by Mikko
    # J.S. Auvinen, MIT License. https://github.com/mjsauvinen/P4UL
    
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

def luo_3dchm(tnimi2d, ptnimi, zp0=0.0, zpm=None, dzp=1.0, dz=None, ulos=None, bmax=9999):
    """Luodaan 3D CHM-tiedosto perustuen profiiliin ja 2D CHM-tiedostoon."""

    A = rxr.open_rasterio(tnimi2d)
    if zpm==None:
        zpm = float(A.isel(band=0).max().data)
    
    p0 = np.loadtxt(ptnimi)
    z0 = np.arange(p0.size)*dzp + zp0

    # Uusi pystyakseli
    if dz is None:
        dz = A.rio.resolution()[0]

    z1 = np.arange(dz, zpm + dz/10, dz)
    p = np.interp(z1, z0, p0)

    # 3D-geotiffit luodaan seuraavasti: Otetaan tuosta data numpy
    # taulukkoon ja missä kohtaa latvustoa on yli z metrin korkeudessa
    # ja laitetaan jokaiseen sellaiseen ruutuun p-taulokosta
    # arvo. Tallennetaan tämä taulukko sitten geotiffinä.

    AAA = A.isel(band=0)*0.0
    for i in range(np.min((z1.size,bmax-1))):   
        AA = A.isel(band=0) - z1[i]
        AA.data[AA.data < 0.0] = 0.0
        AA.data[AA.data > 0.0] = p[i]
        AA.band.data = i+2
        AAA = xr.concat([AAA, AA], dim='band')

    AAA.rio.set_attrs({'dz': dz},inplace=True)

    A.close()

    if ulos is not None:
        AAA.rio.to_raster(ulos, driver='GTiff', compress='ZSTD')

    return AAA
