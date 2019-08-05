# Program to digest make depend files
import os
from typing import List, Set

DirectoryName = str
FileName = str


class AmbiguousFinder:
    """ Find files that exist in more than one directory from a given set of directories"""

    def __init__(self, project_root_directory: DirectoryName):
        """ Initialize a DigestDepends object. """
        self.project_root_directory = project_root_directory
        pass

    def find_ambiguities(self):
        """ Main routine."""
        dir_files = [
            "uniqued-projdirs-CPU_A.txt",
            "uniqued-sysdirs-CPU_A.txt"
        ]
        dirs = []
        for dir_filename in dir_files:
            with open(dir_filename, 'r') as f:
                for line in f:
                    line = line.strip("\n")
                    dirs.append(line)
                    pass
                pass
            pass
        containing_dirs = dict()
        for dir in dirs:

            pass
        pass


if __name__ == u'__main__':
    print('Finding ambiguous files\n')
    finder = AmbiguousFinder(os.getcwd())
    finder.find_ambiguities()
    print('\ndone.\n')
