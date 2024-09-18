# Luokka PIDS-tiedostoja varten

# 18.9.2024
# Jukka-Pekka Keskinen

import xarray as xr
from datetime import datetime, timezone
import yaml

class Pids(xr.Dataset):
    def __init__(self):
        self = xr.Dataset()
        self.attrs['Conventions'] = 'CF-1.7'
        self.attrs['origin_lon'] = 25.74741
        self.attrs['origin_lat'] = 62.24264
        self.attrs['origin_time'] = str(
            datetime.now(timezone.utc).replace(microsecond=0))[:-6] + ' +00'
        self.attrs['origin_x'] = 434918.026949222
        self.attrs['origin_y'] = 6901840.54175464
        self.attrs['origin_z'] = 0.0
        self.attrs['rotation_angle'] = 0.0
        
        return self

    def luku_tiedostosta(self, polku):
        with open(polku, 'r') as f:
            data = yaml.safe_load(f)

        # Globaalit attribuutit
        for i in ['Conventions', 'origin_lon', 'origin_lat',
                  'origin_time', 'origin_x', 'origin_y', 'origin_z',
                  'rotation_angle', 'acronym', 'author', 'campaign',
                  'contact_person', 'comment', 'data_content', 'dependencies',
                  'keywords', 'license', 'location', 'palm_version', 'site',
                  'source', 'title', 'version']:
            if i in data:
                self.attrs[i] = data[i]
            
            
        
    def tallennus(self, polku='PIDS_STATIC'):
        self.attrs['history'] = str(datetime.now().replace(microsecond=0)) + ': File created'
        self.attrs['creation_time'] = str(
            datetime.now(timezone.utc).replace(microsecond=0))[:-6] + ' +00'
        self.to_netcdf(polku)
