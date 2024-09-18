# Luokka PIDS-tiedostoja varten

# 18.9.2024
# Jukka-Pekka Keskinen

import xarray as xr
from datetime import datetime, timezone
import yaml
import os

class Pids(xr.Dataset):
    def __init__(self):
        super().__init__()
        self.attrs['Conventions'] = 'CF-1.7'
        self.attrs['origin_lon'] = 25.74741
        self.attrs['origin_lat'] = 62.24264
        self.attrs['origin_time'] = str(
            datetime.now(timezone.utc).replace(microsecond=0))[:-6] + ' +00'
        self.attrs['origin_x'] = 434918.0
        self.attrs['origin_y'] = 6901840.0
        self.attrs['origin_z'] = 0.0
        self.attrs['rotation_angle'] = 0.0
        

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
                self.attrs[i] = str(data[i])

        # Liukuluvut    
        for i in ['origin_lon', 'origin_lat', 'origin_x', 'origin_y',
                  'origin_z', 'rotation_angle', 'palm_version']:
            if i in data:
                self.attrs[i] = float(data[i])

        # Kokonaisluvut
        if 'version' in data:
            self.attrs['version'] = int(data['version'])

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

            self['crs'] = CRS
        
    def tallennus(self, polku='PIDS_STATIC'):
        self.attrs['history'] = str(datetime.now().replace(microsecond=0)) + ': File created'
        self.attrs['creation_time'] = str(
            datetime.now(timezone.utc).replace(microsecond=0))[:-6] + ' +00'
        self.to_netcdf(polku)
