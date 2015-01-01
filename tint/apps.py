import os
import glob


class AppsList(object):
    def __init__(self, location):
        if not os.path.isdir(location):
            raise RuntimeError("Cannot find apps location %s" % location)
        self.location = location

    def getAppNames(self):
        dirlist = glob.glob(os.path.join(self.location, "*"))
        return [ os.path.basename(fname) for fname in dirlist ]
            

    def __iter__(self):
        for appname in self.getAppNames():
            yield appname
