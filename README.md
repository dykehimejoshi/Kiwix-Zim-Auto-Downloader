# Kiwix Zim Auto-Downloader

This is a script that is used to auto-download the newest version of a specified list of ZIM archives for use with [Kiwix](https://www.kiwix.org).

If you choose to clone this for yourself, you must rename `downloadLinks-example.csv` to `downloadLinks.csv`.

This script reads the `downloadLinks.csv` file in the same directory and downloads them to the same directory.

The syntax of the CSV file is `URL, Name`, where `URL` is the url of the file to download **with no date** (e.g. `https://download.kiwix.org/zim/archlinux_en_all_nopic.zim`).
`Name` is the human-readable name of what the link points to. It's not necessary to use and doesn't need to be correct, but it should be so you know what's being downloaded and which files didn't download in the case of an error.

## Quirks
For now, the script deletes the file in case a new one is found. Because of this, make sure your internet connection is stable for the entirety of the session.

The CSV file for holding the links should begin with `URL,Name` and the links should be correct. There is no checking whether or not a link is accurate, so do your diligence and make sure it's correct.
