"""
This module computes the differences between MathWork's Polyspace Code Prover or Polyspace Bug Finder
checks exported to a file. Such files contain lines of tab-separated fields. The first line has the caption for
the fields in that position. The motivation for this module is that one may run Polyspace multiple times,
perhaps with different configurations or after some source code changes. One then wants to know what affect
the changes had. Typically a change may remove a check (e.g. because more information is given to Polyspace so
it knows the problem cannot happen). Or it might be that the change will cause a check that was previously
conditional to now be certain (orange to red).

Richard L Ford, August 18, 2020
"""

import os
import sys
from typing import Dict, List

# The following are types used to annotate the types of function arguments or return values.
DirectoryName = str
FileName = str


def exported_to_dict(filename: FileName, key_fields: List) -> (Dict, List):
    """
    Read Polyspace check file returning a dictionary of dictionaries and a list of key field names.

    The fields of the first line are the keys to the fields. Each subsequent line
    is made a dictionary that maps those keys to the corresponding field values.

    :param filename: The Polyspace check file to process.
    :param key_fields: A subset of the keys that are sufficient to uniquely identify a finding.
    :return: A pair consisting of a dictionary and a list.
    - The dictionary has an entry for each non-header line in which the key is formed from the
      line using the key_fields (concatenated together), and the value is a dictionary giving
      the values for the fields of that line.
    - The list is the list of keys as extracted from the header line of the file.
    """
    result_dict = {}
    with open(filename, 'r', encoding="latin-1") as f:
        num = 0
        for line in f:
            num = num + 1
            line = line.strip("\\\n")
            fields = line.split('\t')
            if num == 1:
                keys = fields
                keysSet = set(keys)
                for k in key_fields:
                    if k not in keysSet:
                        print(f'key {k} in not in the keysSet')
                continue
            entry = {}
            for i in range(len(keys)):
                entry[keys[i]] = fields[i]
                pass
            keyfieldValues = [entry[k] for k in key_fields]
            entryKey = '\t'.join(keyfieldValues)
            if entryKey in result_dict:
                existing_entry = result_dict[entryKey]
                print(f"Ambiguous data for key={entryKey}, \n    existing={existing_entry}\n    new={entry}\n")
            else:
                result_dict[entryKey] = entry
            pass

    return result_dict, keys


def compare_dicts(d1: Dict, d2: Dict) -> (List, List, List):
    """Compare keys of two dictionaries returning list of keys only in first, only in second, or in both."""
    d1Only = [k for k in d1.keys() if k not in d2]
    d2Only = [k for k in d2.keys() if k not in d1]
    inBoth = [k for k in d1.keys() if k in d2]
    return d1Only, d2Only, inBoth


""" Write dictionary to file.
"""


def write_dicts(field_keys: List, entry_keys: List, d: Dict, filename: FileName):
    """
    Write the specified fields of a specified entries of a dictionary of dictionaries to file.

    :param d: The input dictionary of dictionaries.
    :param entry_keys: A list of keys of d whose corresponding dictionaries are to be output.
    :param field_keys: The fields of the inner dictionaries that are to be output (in the given order).
    :param filename: The name of the file that is to be written.
    :return: Nothing
    """
    with open(filename, "w") as w:
        line = "\t".join(field_keys)
        w.write(line + '\n')
        for entryKey in entry_keys:
            entry = d[entryKey]
            fields = [entry[key] for key in field_keys]
            line = "\t".join(fields)
            w.write(line + '\n')
            pass
    pass


def check_consistency(field_keys: List, entry_keys: List, d1: Dict, d2: Dict):
    """
    Check the consistency of two dictionaries of dictionaries.

    Consistency is checked for outer level entries from entry_keys and inner level entries from field_keys.
    :param field_keys: List selecting the outer level entries to check.
    :param entry_keys: List containing the field keys to check.
    :param d1: The first dictionary of dictionaries to check
    :param d2: The second dictionary of dictionaries to check
    :return: None, but messages are printed out for any inconsistencies found.
    """
    num: int = 0
    numInconsistencies = 0
    for entryKey in entry_keys:
        num = num + 1
        entry1 = d1[entryKey]
        entry2 = d2[entryKey]
        for key in field_keys:
            if key == 'ID':
                continue
            val1 = entry1[key]
            val2 = entry2[key]
            if val1 != val2:
                print(f'Inconsistency with entry {num}, entryKey: {entryKey}, key: {key}, val1: {val2}, val2: {val2}\n')
                numInconsistencies = numInconsistencies + 1
    pass


class PolyDiff:
    """
    Class to hold the context for performing differences between Polyspace check files.
    """

    def __init__(self, project_root_directory: DirectoryName):
        """ Initialize a Polyspace differencer object.

        :param project_root_directory:
        """
        self.project_root_directory = project_root_directory


    def do_diff2(self, dir1: DirectoryName, dir2: DirectoryName, file_root: FileName, diff_dir: DirectoryName):
        """
        Compute and output the differences between two Polyspace check files.

        :param dir1: Relative subdirectory holding the first file.
        :param dir2: Relative subdirectory holding the second file.
        :param file_root: The name of the Polyspace check file (same in each subdirectory)
        :param diff_dir: Relative subdirectory into which the output is written.
        :return: None, but output is written into files.
        """
        fullFile1 = os.path.join(self.project_root_directory, dir1, file_root)
        fullFile2 = os.path.join(self.project_root_directory, dir2, file_root)
        fullDiffDir = os.path.join(self.project_root_directory, diff_dir)
        os.makedirs(fullDiffDir, exist_ok=True)
        keyFields = ["Family", "Detail", "File", "Line", "Col", "Folder", "Class", "Function"]
        d1, d1FieldKeys = exported_to_dict(fullFile1, keyFields)
        d2, d2FieldKeys = exported_to_dict(fullFile2, keyFields)
        # assert (d1FieldKeys == d2FieldKeys)
        d1OnlyKeys, d2OnlyKeys, inBothKeys = compare_dicts(d1, d2)
        out_root = os.path.splitext(file_root)[0]
        write_dicts(d1FieldKeys, d1OnlyKeys, d1, os.path.join(fullDiffDir, out_root + "-d1Only.txt"))
        write_dicts(d2FieldKeys, d2OnlyKeys, d2, os.path.join(fullDiffDir, out_root + "-d2Only.txt"))
        check_consistency(keyFields, inBothKeys, d1, d2)
        write_dicts(d1FieldKeys, inBothKeys, d1, os.path.join(fullDiffDir, out_root + "-inBoth.txt"))
        pass


def usage():
    """ Usage:
    python3 poly-export-diff.py dir1 dir2 file_root diff_dir

    Compares the contents of Polyspace output files

        ./dir1/file_root and ./dir2/file_root

    and produces the following files

        ./diff_dir/root-d1Only.txt
        ./diff_dir/root-d2Only.txt
        ./diff_dir/root-both.txt

    where root is file_root with its file extension removed.
    The output files are in the same format as the input files,
    i.e. tab-separated fields with the first line containing
    the field keys.
    """
    print(usage.__doc__)
    sys.exit(1)


if __name__ == u'__main__':
    if len(sys.argv) != 5:
        usage()

    options = sys.argv[1:]
    (dir1_arg, dir2_arg, file_root_arg, diff_dir_arg) = options

    print('Finding differences in Polyspace result export files\n')
    differ = PolyDiff(os.getcwd())
    differ.do_diff2(dir1_arg, dir2_arg, file_root_arg, diff_dir_arg)
    print('\ndone.\n')
