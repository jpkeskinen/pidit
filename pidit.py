# Käyttöliittymä pidsien luontia varten ja siihen liittyvään
# esikäsittelyyn.

# Jukka-Pekka Keskinen
# 5/2025

import click
import pids

@click.group()
def cli():
    """Yksinkertainen työkalu PIDS_STATIC-tiedostojen luontiin ja siihen liittyvää esikäsittelyyn."""
    pass

@click.command()
@click.argument("asetustiedosto", type=str, required=True)
@click.option("-u", "--ulos","ulos", default="PIDS_STATIC", type=str, show_default=True,
    help="Polku luotavalle PIDS_STATIC-tiedostolle."
)
def tiedostosta(asetustiedosto, ulos):
    """Luo pidit yaml-asetustiedoston perusteella."""

    # Create a PIDS object
    pids_obj = pids.Pids()

    # Read from the input YAML file
    pids_obj.luku_tiedostosta(asetustiedosto)

    # Write to the output PIDS file (if -u/--ulos is provided)
    pids_obj.tallennus(ulos)

@click.command()
@click.argument("chmtiedosto", type=str, required=True)
@click.argument("profiilitiedosto", type=str, required=True)
@click.argument("dz", type=float, required=True)
@click.option("-u", "--ulos","ulos", default=None, type=str, show_default=False,
    help="Polku luotavalle 3D tiedostolle."
)
def CHM3D(chmtiedosto,ulos,profiilitiedosto,dz):
    """Luo 3D CHM-tiedoston 2D CHM-tiedostosta ja profiilista."""
    pids.luo_3dchm(chmtiedosto, profiilitiedosto, dz=dz, ulos=ulos)


cli.add_command(tiedostosta)    
cli.add_command(CHM3D)

    
if __name__ == "__main__":
    cli()




