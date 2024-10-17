# Luokka PIDS-tiedostoja varten

# 18.9.2024
# Jukka-Pekka Keskinen

import xarray as xr
import rioxarray as rxr
from datetime import datetime, timezone
import yaml
import os
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
                    os.exit('CRS-tiedoista puuttuu '+i)                                

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
                    os.exit('CRS-tiedoista puuttuu '+i)                                

            self.xrds['crs'] = CRS

        # Luetaan maanpintatiedot
        if 'dem' in data:
            D = rxr.open_rasterio(data['dem'])
            D = D.isel(band=0).sortby('y')
            if not 'x' in self.xrds.coords and not 'y' in self.xrds.coords:
                self.xrds['zt'] = xr.DataArray( D.data, coords = [
                    ('y', (D.y-D.y[0]).data.astype(np.float32)),
                    ('x', (D.x-D.x[0]).data.astype(np.float32)) ] )
            else:
                os.exit('Koordinaatistot ovat jo olemassa.')

            D.close()
            del D

        # Luetaan latvustotiedot. Siirtymä 2D-rasterista 3D:hen
        # tapahtuu samoin kuin P4UL:ssa.
        if 'chm' in data:
            print('2D-latvustotietoja ei ole vielä toteutettu.')
            os.exit()

        if '3dpad' in data:
            if 'tiedosto' in data['3dpad']:
                D = rxr.open_rasterio(data['3dpad']['tiedosto'])
            else:
                os.exit('3D-tiedoston nimi puuttuu.')

            # Oletetaan, että luettavassa tiedostossa ensimmäine  taso on 0 m.
            if 'dztiff' in data['3dpad']:
                dz0 = float(data['3dpad']['dztiff'])
            else:
                dz0 = 1.0
            
            if 'x' in self.xrds.coords and 'y' in self.xrds.coords:
                if self.xrds.x.size == D.x.size and self.xrds.y.size == D.y.size:
                    T = xr.DataArray( D.data, coords = [
                        ('zlad', dz0*(D.band.data-1).astype(np.float32)),
                        ('y', self.xrds.y), ('x', self.xrds.x) ] )
                else:
                    os.exit('Koordinaatistot eivät täsmää.')
            else:
                T = xr.DataArray( D.data, coords = [
                    ('zlad', dz0*(D.band.data-1).astype(np.float32)),
                    ('y', (D.y-D.y[0]).data.astype(np.float32)),
                    ('x', (D.x-D.x[0]).data.astype(np.float32))  ] )

            # Muokataan z-akseli kuntoon.
            if 'dzpids' in data['3dpad']:
                dz = float(data['3dpad']['dzpids'])
            else:
                dz = dz0

            if 'interpolointi' in data['3dpad']:
                inmen = data['3dpad']['interpolointi']
            else:
                inmen = 'nearest'

            zu = np.append(0.0, np.arange(dz/2, T.zlad[-1]+dz/100, dz, dtype=np.float32) )

            self.xrds['lad'] = T.interp(zlad=zu, method=inmen)

            D.close()
            del D
            del T
            
    def tallennus(self, polku='PIDS_STATIC'):
        self.xrds.attrs['history'] = str(datetime.now().replace(microsecond=0)) + ': File created'
        self.xrds.attrs['creation_time'] = str(
            datetime.now(timezone.utc).replace(microsecond=0))[:-6] + ' +00'
        self.xrds.to_netcdf(polku)
