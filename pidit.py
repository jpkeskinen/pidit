# Käyttöliittymä pidsien luontia varten ja siihen liittyvään
# esikäsittelyyn.

# Jukka-Pekka Keskinen
# 5/2025

import click
import pids

@click.command(help="Yksinkertainen työkalu PIDS_STATIC-tiedostojen luontiin ja siihen liittyvää esikäsittelyyn.")
@click.argument("asetustiedosto", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-u", "--ulos",
    "ulos",
    type=click.Path(writable=True, dir_okay=False),
    help="Polku luotavalle PIDS_STATIC-tiedostolle."
)
def main(asetustiedosto, ulos):
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

if __name__ == "__main__":
    main()




