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

            # Liukulukumoitoiset
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

        # Luetaan latvustotiedot. Siirtymä 2D-rasterista 3D:hen
        # tapahtuu samoin kuin P4UL:ssa.
        if 'chm' in data:
               
             
    def tallennus(self, polku='PIDS_STATIC'):
        self.xrds.attrs['history'] = str(datetime.now().replace(microsecond=0)) + ': File created'
        self.xrds.attrs['creation_time'] = str(
            datetime.now(timezone.utc).replace(microsecond=0))[:-6] + ' +00'
        self.xrds.to_netcdf(polku)
