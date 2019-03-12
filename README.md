# bookPull
This application can generate a list of book publications using eprints data. An example of its output can be found at https://eve.gd/books/ .

## Installation
First, clone the repo to your local machine. Then install the requirements into a virtual environment using pip -r requirements.txt.

## Usage
```
Usage:
  listBooks.py <id_file> <template_file> <output_file> <base_url> [--debug] [--refresh]
  listBooks.py (-h | --help)
  listBooks.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --debug       Enable debug output.
  --refresh     Delete cached versions and do a hard refresh from the eprints server.

Info:

The ID file specified should have a colon-delimited list of eprint record IDs, an image URL, and a link URL.

An example list might look like this:
26645:eve.gd/images/anxietycover.png:eprints.bbk.ac.uk/26645/
21102:eve.gd/images/anxietycover.png:eprints.bbk.ac.uk/21102/
20716:www.sup.org/img/covers/med_large/pid_30253.jpg:www.amazon.co.uk/Close-Reading-Computers-Scholarship-Computational/dp/1503609367/

Note that no field should contain a colon (":").

The template file should have a block of text "[CONTENTS]" within a table.

The base URL should be an eprints repository, like eprints.bbk.ac.uk.
```