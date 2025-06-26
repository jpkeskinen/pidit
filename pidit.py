#!/usr/bin/env python3

# Käyttöliittymä pidsien luontia varten ja siihen liittyvään
# esikäsittelyyn.

# Jukka-Pekka Keskinen
# 2025

import click
import pids

@click.group()
def cli():
    """Yksinkertainen työkalu PIDS_STATIC-tiedostojen luontiin ja siihen liittyvää esikäsittelyyn."""
    pass

@click.command()
@click.argument("asetustiedosto", type=str, required=True)
@click.option("-u", "--ulos","ulos", default="PIDS_STATIC", type=str, show_default=True,
    help="Polku luotavalle PIDS_STATIC-tiedostolle.")
def tiedostosta(asetustiedosto, ulos):
    """Luo pidit yaml-asetustiedoston perusteella.

    ASETUSTIEDOSTO: Polku YAML-asetustiedostoon, joka sisältää PIDS-asetukset.
    """

    # Create a PIDS object
    pids_obj = pids.Pids()

    # Read from the input YAML file
    pids_obj.luku_tiedostosta(asetustiedosto)

    # Write to the output PIDS file (if -u/--ulos is provided)
    pids_obj.tallennus(ulos)

@click.command()  
@click.argument("chmtiedosto", type=str, required=True)
@click.argument("profiilitiedosto", type=str, required=True)
@click.option("-z", "--dz", "dz", default=1.0, type=float, show_default=True,
    help="Ulos tulevan 3D-CHM:n korkeuden askelväli metreissä.")
@click.option("-u", "--ulos","ulos", default="3dchm.tif", type=str, show_default=True,
    help="Polku luotavalle 3D tiedostolle.")
@click.option("-m", "--maksimi", "maksimi", default=100, type=int, show_default=False,
              help="Suurin tasomäärä luotavassa tiffissä.")
def CHM3D(chmtiedosto,ulos,profiilitiedosto,dz,maksimi):
    """Luo 3D CHM-geotiffin 2D CHM-geotiffin ja PAD-profiilin avulla.
    PAD-profiili luetaan tekstimuotoisesta profiilitiedostosta.
    """
    pids.luo_3dchm(chmtiedosto, profiilitiedosto, dz=dz, ulos=ulos, bmax=maksimi)

@click.command()
@click.argument("geotiffi", type=str, required=True)
@click.option("-u", "--ulos","ulos", default="marginaaleilla.tif", type=str, show_default=True,
    help="Polku luotavalle marginaalit sisältävälle geotiffille.")
@click.option("-m", "--marginaali", "marginaali", default=10, type=int, show_default=True,
    help="Marginaalien koko pikseleinä (esim. 10).")
def marginaalit(geotiffi,ulos, marginaali):
    """Lisää geotiffiin marginaalit syklisiä simulaatioita varten."""
    pids.marginaalit(geotiffi, pak=marginaali,ulos=ulos)


    
cli.add_command(tiedostosta)    
cli.add_command(CHM3D)
cli.add_command(marginaalit)

if __name__ == "__main__":
    cli()




