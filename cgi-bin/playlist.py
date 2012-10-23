#!/usr/bin/env python

# Davd Cain
# RE357
# 2012-10-09

"""
A script to make a m3u bookmark playlist (playable in VLC)

Note that each bookmark should probably have a value for a "bytes"
attribute, but it seems to work without it.
"""

from collections import OrderedDict
from datetime import datetime
import cgi
import csv
import os
import sys
import tempfile
import traceback

hms = "%H:%M:%S"
ms = "%M:%S"

movie_start = datetime.strptime("00:00:00", hms)


class CSVError(Exception):
    pass


def get_clip_dict(csv_file):
    clip_dict = OrderedDict()

    clips_csv = csv.reader(csv_file)

    for num, line in enumerate(clips_csv, start=1):
        if len(line) > 3:
            raise CSVError("Too many columns on line %i (check commas!)" % num)
        elif len(line) < 3:
            raise CSVError("Fewer than three columns on line %i" % num)

        start, end, clip_name = line
        start_time = seconds(start)
        timename = "%s-%s" % (start, end)
        bookmark_name = "%s - %s" % (timename, clip_name)
        clip_dict[start_time] = bookmark_name
    return clip_dict


def make_m3u(clips, title, filmpath):
    print "#EXTM3U"
    print "#EXTINF:7061,%s" % title

    # Bookmarks
    print "#EXTVLCOPT:bookmarks=",  # trailing comma is key
    bookmarks = ["{name=%s,time=%i}" % (name, time) for (time, name) in clips]
    print ",".join(bookmarks)

    # Path to file
    print filmpath


def seconds(clip_start):
    try:
        bookmark_time = datetime.strptime(clip_start, hms)
    except ValueError:
        try:
            bookmark_time = datetime.strptime(clip_start, ms)
        except ValueError:
            print "Invalid time format '%s'. Enter time in H:M:S, or M:S" % clip_start
            raise

    return int((bookmark_time - movie_start).total_seconds())


def main():
    form = cgi.FieldStorage()

    film_title = form["title"].value
    movie_path = form["movie_path"].value
    clip_order = form["clip_order"].value

    outname = "bookmarks.m3u"
    user_csv = form["csv_file"].file

    # Quit if CSV file is empty
    if not (user_csv and user_csv.read()):
        html_err("No CSV file given.")
        return
    user_csv.seek(0)

    # Raise error if path is left as example path
    if not movie_path or movie_path == "/Users/suzieq/East_of_Eden.m4v":
        html_err("Please supply the path to your film.\n"
                '<a href="/gen_clips.html#full_path">Getting the full path of a file</a>')
        return

    # Hack to force universal line support
    fileno, filename = tempfile.mkstemp()
    with open(filename, "w") as newline_file:
        newline_file.write(user_csv.read())
    os.close(fileno)
    csv_file = open(filename, "rU")

    # Parse CSV, crash if errors
    try:
        clip_dict = get_clip_dict(csv_file)
    except CSVError, msg:
        html_err(msg)
        return

    # Sort clips chronologically, if specified
    if clip_order == "chronological":
        clips = sorted(clip_dict.items())
    else:
        clips = clip_dict.items()

    if len(clips) == 0:
        html_err("No clips were found in the CSV file!")
        return

    print 'Content-Type:text/enriched; filename="%s"' % outname
    print 'Content-Disposition: attachment; filename="%s"\n' % outname
    make_m3u(clips, film_title, movie_path)


def text_err(msg):
    print 'Content-Type:text/plain\n'
    print "Error:\n"
    print msg


def html_err(msg):
    print 'Content-Type:text/html\n'
    print "<html>\n<body>"
    print "<h1>Error:</h1>\n"
    print "<p>\n" + msg + "\n</p>"
    print "</body>\n</html>"


if __name__ == "__main__":
    try:
        main()
    except:
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
