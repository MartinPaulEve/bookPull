"""Book release generator.

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

"""
import os
from docopt import docopt
import logging
import pygogo as gogo
import requests
from bs4 import BeautifulSoup


app = "Book List Generator 1.0"

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)

logger = gogo.Gogo(
    'Book List Generator',
    low_formatter=formatter,
    high_formatter=formatter,
    monolog=True).logger


def main(args):
    if '--debug' in args and args['--debug']:
        logger.setLevel('DEBUG')
    else:
        logger.setLevel('INFO')

    logger.info(app)

    # load the template
    logger.debug('Loading template file')

    try:
        with open(args["<template_file>"], "r") as template_file:
            template = template_file.read()
    except EnvironmentError:
        logger.error('Cannot open template file')
        logger.info('Shutting down')
        return

    id_list = []

    # load the ID file
    logger.debug('Loading ID file')

    try:
        with open(args["<id_file>"], "r") as id_file:
            ids = id_file.readlines()

            for id_full in ids:

                release_id = id_full.split(":")

                if not len(release_id) == 3:
                    logger.error("ID line {0} is malformed".format(id_full))
                    logger.info('Shutting down')
                    return

                id_list.append(release_id[0])

                # fetch book
                logger.debug("Fetching book {0}".format(release_id[0]))
                if not fetch_book(args["<base_url>"], release_id, args["--refresh"]):
                    return

                # fetch cover
                logger.debug("Fetching cover art for {0}".format(release_id[0]))
                if not fetch_cover(release_id, args["--refresh"]):
                    return

    except EnvironmentError:
        logger.error('Cannot open ID file')
        logger.info('Shutting down')
        return

    # now build the HTML
    logger.debug("Building output HTML")
    output_html = generate_html(id_list)

    # replace the output template
    logger.debug("Substituting contents in template")
    template = template.replace('[CONTENTS]', output_html)

    # write to a file
    logger.debug("Writing output")
    try:
        with open(args["<output_file>"], "w") as out_file:
            out_file.write(template)
    except EnvironmentError:
        logger.error('Cannot open output file: {0}'.format(args["<output_file>"]))
        logger.info('Shutting down')
        return

    logger.info("Done")


def generate_html(id_list):
    first_td = ['', '']
    second_td = ['', '']
    td_first = ''
    td_second = ''
    output_html = ''
    for release_id in id_list:
        try:
            with open("{0}.data".format(release_id), "r") as in_file:
                fields = in_file.read().split("\n")

                title = fields[0]
                press = fields[1]
                year = fields[2]
                url = fields[3]

                td_first = ' <td><a href="https://{0}"><img itemprop="image" src="{1}" alt="{2}" ' \
                           'style="width:150px;max-width:150px;height:231px" /></a></span></td>'.format(url,
                                                                                                        release_id,
                                                                                                        title)

                td_second = '<td style="padding-bottom: 15px;"><a href="https://{0}">{1}</a>' \
                            '<br />({2}, {3})</td>'.format(url, title, press, year)

                new_output_html, first_td, second_td = process_arrays(first_td, second_td, td_first, td_second)
                output_html += new_output_html
        except EnvironmentError:
            logger.error('Cannot write data file for {0}'.format(release_id))
            logger.info('Shutting down')
            return False

    # at this point, we need to check whether to write the final line
    if first_td[0] == '':
        # do nothing
        pass
    elif first_td[1] == '':
        # one is loaded, the other empty
        logger.debug("Building last blank entry")
        td_first = '<td></td>'
        td_second = '<td style="padding-bottom: 15px;"></td>'
        new_output_html, first_td, second_td = process_arrays(first_td, second_td, td_first, td_second)
        output_html += new_output_html
    else:
        # both loaded
        new_output_html, first_td, second_td = process_arrays(first_td, second_td, td_first, td_second)
        output_html += new_output_html
    return output_html


def fetch_cover(release_id, refresh=False):
    if not os.path.isfile(release_id[0]) or refresh:
        logger.debug("Hard refreshing cover art for {0}".format(release_id[0]))
        try:
            url = "https://{0}".format(release_id[1])
            logger.debug("Fetching {0}".format(url))
            data = requests.get(url, stream=True)
        except requests.RequestException as exc:
            logger.error("Error fetching cover art for {0}. Attempting http.".format(release_id[0]))
            try:
                url = "http://{0}".format(release_id[1])
                logger.debug("Fetching {0}".format(url))
                data = requests.get(url, stream=True)

            except requests.RequestException as second_exc:
                logger.error(second_exc)
                logger.info('Shutting down')
                return False

        try:
            with open(release_id[0], "wb") as out_file:
                for chunk in data.iter_content(chunk_size=128):
                    out_file.write(chunk)
        except EnvironmentError:
            logger.error('Cannot write cover art for {0} to file'.format(release_id[0]))
            logger.info('Shutting down')
            return False
    else:
        logger.debug("Using pre-fetched cover art for {0}".format(release_id[0]))

    return True


def fetch_book(base_url, release_id, refresh=False):
    if not os.path.isfile("{0}.data".format(release_id[0])) or refresh:
        logger.debug("Hard refreshing data for {0}".format(release_id[0]))
        try:
            url = "https://{0}/{1}/".format(base_url, release_id[0])
            logger.debug("Fetching {0}".format(url))
            response = requests.get(url).text
            soup = BeautifulSoup(response, 'html.parser')
        except requests.RequestException as exc:
            logger.error("Error fetching data for {0}".format(release_id[0]))
            logger.error(exc)
            logger.info('Shutting down')
            return False
        except:
            logger.error("Broad error fetching data for {0}".format(release_id[0]))
            logger.info('Shutting down')
            return False

        try:
            with open("{0}.data".format(release_id[0]), "w") as out_file:
                title = soup.find("meta", {"name": "eprints.title"})["content"]
                publisher = soup.find("meta", {"name": "eprints.publisher"})["content"]
                year = soup.find("meta", {"name": "eprints.date"})["content"].split("-")[0]
                out_file.writelines('\n'.join([title, publisher, year, release_id[2]]))
        except EnvironmentError:
            logger.error('Cannot write data for {0} to file'.format(release_id[0]))
            logger.info('Shutting down')
            return False
    else:
        logger.debug("Using pre-fetched data for {0}".format(release_id[0]))

    return True


def process_arrays(first_td, second_td, td_first, td_second):
    output_html = ""
    if first_td[0] == '':
        logger.debug("Loading to first TD")
        first_td[0] = td_first
    elif first_td[1] == '':
        logger.debug("Loading to second TD")
        first_td[1] = td_first

    if second_td[0] == '':
        second_td[0] = td_second
    elif second_td[1] == '':
        logger.debug("Array is loaded so building and emptying")
        second_td[1] = td_second
        # the array is loaded so append the output
        tr_first = "<tr>{0}{1}</tr>".format(first_td[0], first_td[1])
        tr_second = "<tr>{0}{1}</tr>".format(second_td[0], second_td[1])

        output_html += tr_first
        output_html += tr_second

        # unload the arrays
        first_td = ['', '']
        second_td = ['', '']

    return output_html, first_td, second_td


if __name__ == "__main__":
    arguments = docopt(__doc__, version=app)
    main(arguments)
