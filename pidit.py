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
    if ulos:
        pids_obj.tallennus(ulos)
    else:
        # Handle case if no output file is specified:
        click.echo("Virhe: Tulos-tiedostoa ei annettu (--ulos)")
        raise click.UsageError("Anna tulostiedosto -u / --ulos option avulla.")

cli.add_command(tiedostosta)    
    

if __name__ == "__main__":
    cli()




