
# Program to digest make depend files
import os
import re
import sys
from typing import Dict, List, Set
from collections import defaultdict

DirectoryName = str
FileName = str

if __name__ == u'__main__':
    print('Digesting dependency files\n')
    digester = DigestDepends(os.getcwd(), '')
    digester.process_depend_files()
    print('\ndone.\n')
