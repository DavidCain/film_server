#!/usr/bin/env python

# Davd Cain
# RE357
# 2012-10-23

"""
A script to make a m3u bookmark playlist (playable in VLC), or .m4v
video clip files

Note that each bookmark should probably have a value for a "bytes"
attribute, but it seems to work without it.
"""

from collections import OrderedDict
from datetime import datetime
import cgi
import csv
import os
import subprocess
import sys
import tempfile
import traceback
import zipfile

hms = "%H:%M:%S"
ms = "%M:%S"

movie_start = datetime.strptime("00:00:00", hms)


class CSVError(Exception):
    pass


def get_clip_dict(csv_file, give_times=False):
    clip_dict = OrderedDict()

    clips_csv = csv.reader(csv_file)

    for num, line in enumerate(clips_csv, start=1):
        if len(line) > 3:
            raise CSVError("Too many columns on line %i (check commas!)" % num)
        elif len(line) < 3:
            raise CSVError("Fewer than three columns on line %i" % num)

        start, end, name = line
        timename = "%s-%s" % (start, end)
        clip_name = "%s - %s" % (timename, name) if give_times else name
        clip_dict[get_time(start)] = (get_time(end), clip_name)
    return clip_dict


def make_m3u(clips, title, filmpath):
    print "#EXTM3U"
    print "#EXTINF:7061,%s" % title

    # Bookmarks
    print "#EXTVLCOPT:bookmarks=",  # trailing comma is key
    bookmarks = ["{name=%s,time=%i}" % (name, seconds(start)) for start, (end, name) in clips]
    print ",".join(bookmarks)

    # Path to file
    print filmpath


def make_clips(clips, film_title):
    film_path = "/srv/ftp/%s.m4v" % film_title

    base, extension = os.path.splitext(film_path)  # excessive, but an example

    clip_files = []

    for start, (end, clip_name) in clips:
        running_time = str(end - start)  # Will be in HMS
        start = str(start)
        clip_fn = clean_path(clip_name)

        outfile = "/clips/%s" % clip_fn + extension

        # Use subprocess for better error handling
        subprocess.check_call(['ffmpeg', '-ss', start, '-t', running_time,
            '-i', film_path, '-acodec', 'copy', '-vcodec', 'copy', outfile])

        #raise Exception("Error creating clip '%s'; contact David." % clip_name)
        clip_files.append(outfile)

    fd, zip_path = tempfile.mkstemp()
    ret_zip(zip_path, clip_files)
    os.close(fd)
    for line in open(zip_path):
        print line,

    os.remove(zip_path)


def ret_zip(zip_fn, paths):
    zip = zipfile.ZipFile(zip_fn, 'w')
    for path in paths:
        zip.write(path)
    zip.close()


def clean_path(path):
    """ Sanitize the path for sensible names. """
    cleaned = path.replace(":", "-")
    cleaned = cleaned.replace(" ", "_")
    cleaned = cleaned.replace("/", "-")
    cleaned = cleaned.replace("\\", "-")
    cleaned = cleaned.replace("..", "")
    cleaned = cleaned.replace("?", "")
    return cleaned


def seconds(delta):
    return int(delta.total_seconds())


def get_time(clip_start):
    try:
        bookmark_time = datetime.strptime(clip_start, hms)
    except ValueError:
        try:
            bookmark_time = datetime.strptime(clip_start, ms)
        except ValueError:
            print "Invalid time format '%s'. Enter time in H:M:S, or M:S" % clip_start
            raise

    return bookmark_time - movie_start


def main():
    form = cgi.FieldStorage()

    film_title = form["title"].value

    movie_path = form["movie_path"].value
    clip_order = form["clip_order"].value
    output_type = form["output_type"].value

    user_csv = form["csv_file"].file

    # Quit if CSV file is empty
    if not (user_csv and user_csv.read()):
        html_err("No CSV file given.")
        return
    user_csv.seek(0)

    # Raise error if path is left as example path
    if (output_type == "playlist" and (not movie_path or
            movie_path == "/Users/suzieq/East_of_Eden.m4v")):
        html_err("Playlists require the path to your film.\n"
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

    # Give the result as downloadable
    outname = "booxmarks.m3u" if output_type == "playlist" else "clips.zip"
    print 'Content-Type:text/enriched; filename="%s"' % outname
    print 'Content-Disposition: attachment; filename="%s"\n' % outname
    if output_type == "playlist":
        make_m3u(clips, film_title, movie_path)
    elif output_type == "clips":
        make_clips(clips, film_title)


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
