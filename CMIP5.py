import py7zlib

class Reader(object):
    def __init__(self,basepath="/work/cmip5/",archive_path="$(basepath)/_archive"):
        self.basepath=basepath
        self._archive= archive_path
