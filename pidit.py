# Käyttöliittymä pidsien luontia varten.

# Jukka-Pekka Keskinen
# 13.5.2025

import argparse
import pids

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Yksinkertainen työkalu PIDS_STATIC-tiedostojen luontiin.")
    parser.add_argument(
        "asetustiedosto", type=str, help="Polku asetustiedostoon (YAML-muodossa)"
    )
    parser.add_argument(
        "-u","--ulos", type=str, help="Polku luotavalle PIDS_STATIC-tiedostolle."
    )
    args = parser.parse_args()

    # Create a PIDS object
    pids_obj = pids.Pids()

    # Read from the input YAML file
    pids_obj.luku_tiedostosta(args.input_file)

    # Write to the output PIDS file
    pids_obj.tallennus(args.output_file)
