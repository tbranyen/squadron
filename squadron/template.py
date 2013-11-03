import os
import errno
from shutil import copyfile
from quik import Template, FileLoader
import urllib
import autotest

def mkdirp(dirname):
    try:
        os.mkdir(dirname)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(dirname):
            pass

def ext_template(loader, inputhash, relpath, cur, dest):
    template = loader.load_template(relpath)
    output = template.render(inputhash, loader=loader)

    finalfile = dest.rstrip('.tpl')
    with open(finalfile, 'w') as outfile:
        outfile.write(output)
        return finalfile

def ext_download(loader, inputhash, relpath, cur, dest):
    with open(cur, 'r') as downloadfile:
        # split on whitespace
        (url, checksum) = downloadfile.read().split(None, 3)

        finalfile = dest.rstrip('.download')
        urllib.urlretrieve(url, finalfile)
        return finalfile

extension_handles = {'tpl' : ext_template, 'download' : ext_download}

def get_ext(filename):
    root,ext = os.path.splitext(filename)
    if ext.lower() in ['.gz', '.bz2', '.xz']:
        other = os.path.splitext(root)[1]
        if other.lower() in ['.tar']:
            return (other[1:] + ext).lower()

    return ext[1:].lower()

class DirectoryRender:
    def __init__(self, basedir):
        self.loader = FileLoader(basedir)
        self.basedir = basedir

    def render(self, destdir, inputhash, currpath = ""):
        """
        Transforms all templates and downloads all files in the directory
        supplied with the input values supplied. Output goes in destdir.

        Keyword arguments:
            destdir -- the directory to put the rendered files into
            inputhash -- the dictionary of input values
        """
        items = os.listdir(os.path.join(self.basedir, currpath))

        for filename in items:
            relpath = os.path.join(currpath, filename)
            cur = os.path.join(self.basedir, relpath)
            dest = os.path.join(destdir, relpath)
            if os.path.isdir(cur):
                mkdirp(dest)
                self.render(destdir, inputhash, relpath)
            else:
                ext = get_ext(filename)
                if ext in extension_handles:
                    finalfile = extension_handles[ext](self.loader, inputhash, relpath, cur, dest)
                    finalext = get_ext(finalfile)

                    if finalext in autotest.testable:
                        if not autotest.testable[finalext](finalfile):
                            raise ValueError('File {} didn\'t pass validation for {}'.format(finalfile, finalext))
                else:
                    copyfile(cur, dest)

