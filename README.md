## About

This repository contains the HTML pages and a CGI script that drive a
video clip-generating GNU/Linux file server.

The HTML page `gen_clips.html` presents a simple user interface to 
specify desired clips in a feature film and the CGI script does all the
work to generate these clips in two downloadable formats.

### Interface

The main HTML page, and interface to users:

![Form](https://raw.github.com/DavidCain/film_server/master/interface.png)

## Installation

The server assumes the existence of several `.m4v` feature-length films
in `/srv/ftp/` (this path can be changed in the cgi script). If video
clips are desired, system calls are made to `ffmpeg` (tested on v.
0.8.3-4).

### Dependencies
- Python 2.7
- Apache 2 (with Python support)
- ffmpeg (for video clips only)

Files in `www` belong in `/var/www/`, or anywhere Apache serves pages.
`playlist.py` should be stored in `/usr/lib/cgi-bin/`, or wherever
cgi-bin scripts are configured to reside.
