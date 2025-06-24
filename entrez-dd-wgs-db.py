import argparse
import csv
import subprocess
import os
import time
import re

# Function to sanitize the ID string (replace spaces with underscores, non-alphanumeric with "-")
def sanitize_id(id_string):
    id_string = id_string.replace(" ", "_")  # Replace spaces with underscores
    return re.sub(r"[^a-zA-Z0-9_]", "-", id_string)  # Replace non-alphanumeric symbols with "-"

# Set up argument parser
parser = argparse.ArgumentParser(description="Generate and execute Entrez Direct commands from CSV accession list.")
parser.add_argument("-i", "--input", required=True, help="Input CSV file containing accession numbers and IDs")
args = parser.parse_args()

# Read CSV file, ignoring blank rows
accession_data = []
with open(args.input, "r") as infile:
    reader = csv.DictReader(infile)
    for row in reader:
        accession = row["accession"].strip()
        identifier = sanitize_id(row["id"].strip())  # Sanitize ID
        if accession and identifier:
            output_filename = f"{accession}_{identifier}.fasta"
            accession_data.append((accession, output_filename))

# Generate commands file
commands_file = "commands.txt"
with open(commands_file, "w") as outfile:
    for accession, output_filename in accession_data:
        outfile.write(f"esearch -db nucleotide -query {accession} | efetch -format fasta > {output_filename}\n")

print(f" Commands generated in '{commands_file}'.")

# Execute commands sequentially, ensuring each command outputs a file before proceeding
total_commands = len(accession_data)
for index, (accession, output_filename) in enumerate(accession_data, start=1):
    command = f"esearch -db nucleotide -query {accession} | efetch -format fasta > {output_filename}"
    
    print(f" Running ({index}/{total_commands}): {command}")
    subprocess.run(command, shell=True, check=True)

    # Wait until the output file is created before proceeding
    while not os.path.exists(output_filename):
        time.sleep(1)  # Prevent excessive CPU usage while checking
    
    print(f" Completed ({index}/{total_commands}): {output_filename} downloaded.\n")

    # Modify the first line of the FASTA file
    with open(output_filename, "r") as fasta_file:
        lines = fasta_file.readlines()
    if lines and lines[0].startswith(">"):
        lines[0] = f">{output_filename[:-6]}\n"  # Replace header with output filename (minus ".fasta")

    # Write the modified FASTA file
    with open(output_filename, "w") as fasta_file:
        fasta_file.writelines(lines)

    print(f" Updated FASTA header in '{output_filename}'.")

print(" Fasta files downloaded. All commands executed successfully!")