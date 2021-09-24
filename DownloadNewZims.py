#!/usr/bin/env python3
## Downloads all the latest specified zim files from Kiwix.

# Used for downloading the files
import requests

# Used for verifying checksums
import hashlib

# Used to check if a file exists or not and for removing files
import os

# Used for moving temp download file to current directory
# Needed if running from a USB, for example
import shutil

# Used for finding the size of the objects we download
from sys import getsizeof

# Used for reading the file with links
import csv

# Used for calculating time spent downloading a file
from time import perf_counter

# Links:
# Note: Ending the links with ".sha256" will get their hash file, used for verification.
# Please appreciate this line used to clean up this script: nnoremap ,go 0/,<CR>nv$hxj
links = []

# Read in the file with links to download
csv_fname = "downloadLinks.csv"
first_line = True
ttd = 0 # total to download
with open(csv_fname, 'r') as csf:
    while True:
        line = csf.readline()
        if first_line:
            # Remove the header line ("URL,Name")
            first_line = False
            continue
        if not line:
            break
        if line.startswith('#'):
            # Ignore lines starting with a hash
            continue
        entry = line.split(',')
        links.append([entry[0].strip(), entry[1].strip()])
        # Calculate the total size of the zims
        ttd += 1

print("Total to check:", ttd)

# Global variables for seeing how much data we read and download
total_down = 0

# In the event that there's an error on Kiwix's end, alert the user at the end (0 = no error, 1 = error)
kiwix_err = 0

def download_zim(item):
    def get_hash(b):
        #= lambda b: hashlib.sha256(b).hexdigest() # the old one-liner
        # Using the second method to calculate sha256 sums from here:
        # https://www.quickprogrammingtips.com/python/how-to-calculate-sha256-hash-of-a-file-in-python.html
        sha256_hash = hashlib.sha256()
        with open(b, 'rb') as f:
            # Read and update hash string value in blocks of 4096
            for byte_block in iter(lambda: f.read(8192), b''):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def actually_download():
        print("Downloading", url, "...")
        tmppath = '/tmp/' + fname + '.part'
        if os.path.isfile(tmppath):
            os.remove(tmppath)
        try:
            start_time = perf_counter() # start time for calculating time spent downloading a file
            sha256_hash = hashlib.sha256() # calculate the hash while downloading
            # Adapted from:
            #   https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests#16696317
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                # the Content-Length header gives the length of the content in bytes
                content_length = int(r.headers['Content-Length'])
                downloaded_size = content_length / (1024 ** 2) # downloaded size in MB (or MiB idk)
                #print('Content-Length:', r.headers['Content-Length']) # for debugging
                print("%.2f" % (downloaded_size), "MB to download")
                # Assuming we have write permissions in the /tmp directory
                with open(tmppath, 'wb') as f:
                    chunk_bytes = 8192
                    # variables used for calculating percentage complete
                    chunks_downloaded = 0
                    approx_chunks = ((content_length / 8192) // 1)
                    for chunk in r.iter_content(chunk_size=chunk_bytes):
                        # If you have chunk encoded response uncomment if
                        # and set chunk_size parameter to None.
                        #if chunk:
                        f.write(chunk)
                        # Calculate hash while downloading
                        sha256_hash.update(chunk)
                        print('\r{:6.2f}% ({:.0f} / {:.0f} chunks) {:.0f}s'.format((chunks_downloaded/approx_chunks)*100, chunks_downloaded, approx_chunks, perf_counter() - start_time), end='')
                        chunks_downloaded += 1
            print()
            global total_down
            total_down += downloaded_size
            fhash = sha256_hash.hexdigest()
            print("Downloaded hash:", shasum[0])
            print("Got hash:\t", fhash)
            if fhash == downloaded_hash:
                print("OK hash for", fname)
                print("Successfully downloaded", url)
                # Remove the old out-of-date file
                if os.path.isfile("./" + fname):
                    os.remove('./' + fname)
                # If the hash is good, move the file from tmp to current directory
                # Use shutil here because we may be operating from a USB drive,
                #   and os.rename/os.replace doesn't work cross-filesystem
                shutil.move(tmppath, fname)
                return 0
            else:
                os.remove(tmppath)
                # Prepending spaces may make it easier to see that something has happened at a glance
                print("\n\t *** [!!] Hash verification FAILED for", fname, '***')
                print("(Old file not removed)")
                print(' '.join(shasum))
                return -1
        except ConnectionError as ce:
            print("[!] Connection error:", str(ce))
            del ce
            raise
        except requests.exceptions.RequestException as re:
            print("[!] Request Exception:", str(re))
            del re
            raise
        except KeyboardInterrupt:
            if os.path.isfile(tmppath): os.remove(tmppath)
            raise
        except Exception as e:
            print("[!] Error:", str(e))
            del e

    # Set up some vars to refer back to
    url = item[0]
    fname = url.split('/')[-1]

    # Download the sha256 hash for verification
    sha = url + ".sha256"
    print("Downloading", sha, "...")
    # we don't include the size of the hash because we don't write it to disk
    r = requests.get(sha)
    shasum = r.text.split(' ')   # shasum = [hash_58fa685ba567..., name_of.file]
    downloaded_hash = shasum[0]
    # XXX There is a weird error where it appears as though some archives return a 404 when trying to download, even if they exist.
    # Try to see if the shasum starts with `<!DOCTYPE', and if it does, skip and return an error.
    if downloaded_hash == "<!DOCTYPE":
        print("    [!!] Error downloading: Error with Kiwix's servers; not continuing.")
        global kiwix_err
        kiwix_err = 1
        print(' '.join(shasum))
        return -2

    # Finding out if the file already exists
    try:
        if os.path.isfile("./" + fname):
            print("File exists, seeing whether it is recent...")
            inhash = get_hash(fname)
            if inhash == downloaded_hash:
                print(fname, "has same hash, skipping.")
                return 0
            else:
                # It doesn't have the same hash, so go ahead and download it again
                print(fname, "is out of date, replacing.")
                #os.remove("./" + fname)
                return actually_download()
        else:
            # If the file doesn't exist in the first place, download it
            return actually_download()
    except MemoryError as me:
        print("[!] Memory Error:", str(me))
        del me
        return -2
    except KeyboardInterrupt:
        # Pressing C-c while checking the file hash will skip it.
        return
    except Exception as e:
        print("[!] Error:", str(e))
        del e
        return -1


# Loop through the array and download the files. If an error occurs, note it and redo it later.
errors = []
count = 0
for l in links:
    count = count + 1
    print(f"# {count}/{ttd}")
    try:
        ret = download_zim(l)
        if ret == -1:
            errors.append(l)
        print()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected, exiting")
        break
    except Exception as ex:
        print("[!] Error:", str(ex))

# If even after attempting to fix an error after three times it fails, give a list of what failed at the end of the session.
meta_errors = []
if errors:
    print("Errors found:")
    try:
        for e in errors:
            try:
                # Try three more times to fix any errors
                for try_num in range(3):
                    ret = download_zim(e)
                    if ret and try_num == 2:
                        meta_errors.append(e[1])
                    if not ret: # ret = 0 (what we want)
                        break
            except KeyboardInterrupt:
                raise
                break
            except Exception as ex:
                print("[!] Error:", str(ex))
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected, exiting")

print("\nDownloading done.")
if meta_errors:
    print("The following files could not be successfully downloaded:")
    for me in meta_errors:
        print(' *', me)
if kiwix_err:
    print("[!] There was an error with Kiwix and some content did not download; try again later.")
if total_down:
    print("Total data downloaded: %.2f MB" % (total_down))
