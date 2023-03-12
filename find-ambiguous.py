# Program to digest make depend files
import os
import re
import sys
from typing import List, Set

DirectoryName = str
FileName = str


class AmbiguousFinder:
    """
    Find files that exist in more than one subdirectory directory of a given directory.
    As input, give a file that is the result of 'find -type f'.
    """

    def __init__(self, pattern: str, root_dir: DirectoryName, out_file: FileName):
        """ Initialize a DigestDepends object. """
        self.pattern = re.compile(pattern)
        self.root_dir = root_dir
        self.out_file = out_file
        self.file_list = []
        self.base_map = {}
        pass

    def find_files(self):
        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                if self.pattern.match(file):
                    self.file_list.append(os.path.join(root, file))
        pass

    def find_ambiguities(self):
        """ Look for ambiguities in the file_list"""
        file_map = {}
        for line in self.file_list:
            line = line.strip("\n")
            basename = os.path.basename(line)
            if basename in file_map:
                dirs = file_map[basename]
                dirs.append(line)
            else:
                file_map[basename] = [line]
        num_ambiguous = 0
        if self.out_file == "-":
            f = sys.stdout
        else:
            f = open(self.out_file, "w")

        for key, value in file_map.items():
            num_dirs = len(value)
            if num_dirs > 1:
                num_ambiguous += 1
                f.write(f"#{num_ambiguous}:{key} is found in {num_dirs} directories\n")
                for i in range(num_dirs):
                    f.write(f"    [{i}]={value[i]}\n")
        f.write(f"Total ambiguous = {num_ambiguous}\n")

if __name__ == u'__main__':
    print('Finding ambiguous files\n')
    if len(sys.argv) != 4:
        print("Usage: find-ambiguous.py <pattern> <directory> (<outputfile>|-)")
        exit(1)

    pattern = sys.argv[1]
    root_dir = sys.argv[2]
    out_file = sys.argv[3]
    finder = AmbiguousFinder(pattern, root_dir, out_file)
    finder.find_files()
    finder.find_ambiguities()
    print('\ndone.\n')
