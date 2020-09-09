"""
This module combines the information on uncalled or unreached functions from Polyspace check output files.

Richard L Ford, August 18, 2020
"""

import os
import sys
from typing import Dict, List, Set

# The following are types used to annotate the types of function arguments or return values.
DirectoryName = str
FileName = str


def exported_to_dict(filename: FileName, keep_fields: List) -> Dict:
    """
    Read Polyspace check file returning a dictionary of dictionaries and a list of key field names.

    The fields of the first line are the keys to the fields. Each subsequent line
    is made a dictionary that maps those keys to the corresponding field values.

    :param filename: The Polyspace check file to process.
    :param keep_fields: A subset of the keys that we want to keep.
    :return: A pair consisting of a dictionary and a list.
    - The dictionary has an entry for each non-header line in which the key is function name
      and the value is a dictionary giving the values for the fields that are kept for that line.
    """
    result_dict = {}
    keep_set : Set = set(keep_fields)
    assert("Function" in keep_set)
    with open(filename, 'r', encoding="latin-1") as f:
        num = 0
        for line in f:
            num = num + 1
            line = line.strip("\\\n")
            fields = line.split('\t')
            if num == 1:
                keys = fields
                keysSet = set(keys)
                for k in keep_fields:
                    if k not in keysSet:
                        print(f'key {k} in not in the keysSet')
                continue
            entry = {}
            for i in range(len(keys)):
                key = keys[i]
                if key in keep_set:
                    entry[key] = fields[i]
                pass
            the_function = entry["Function"]
            if the_function in result_dict:
                existing_entry = result_dict[the_function]
                print(f"Ambiguous data for key={the_function}, \n    existing={existing_entry}\n    new={entry}\n")
            else:
                result_dict[the_function] = entry
            pass

    return result_dict


def combine_dicts(d1: Dict, d2: Dict) -> Dict:
    """Compare keys of two dictionaries returning list of keys only in first, only in second, or in both."""
    result_dict = {}
    for k in d1.keys():
        result_dict[k] = d1[k]
    for k in d2.keys():
        if k in result_dict:
            print(f"Duplicate function: {k}\n")
        else:
            result_dict[k] = d2[k]
    return result_dict

def write_dicts(keep_fields: List, d: Dict, filename: FileName):
    """
    Write the specified fields of a specified entries of a dictionary of dictionaries to file.

    :param d: The input dictionary of dictionaries.
    :param keep_fields: The fields t keep in order
    :param filename: The name of the file that is to be written.
    :return: Nothing
    """
    entry_keys: List = sorted(d.keys())
    with open(filename, "w") as w:
        line = "\t".join(keep_fields)
        w.write(line + '\n')
        for entryKey in entry_keys:
            entry = d[entryKey]
            fields = [entry[key] for key in keep_fields]
            line = "\t".join(fields)
            w.write(line + '\n')
            pass
    pass


class PolyFunc:
    """
    Class to hold the context for performing differences between Polyspace check files.
    """

    def __init__(self, ):
        """ Initialize a Polyspace differencer object."""
        pass

    def do_function_analysis(self, in_file1: FileName, in_file2: FileName, out_file: FileName):
        """Combine function information from in_file1 and in_file2 and output it to out_file"""
        keep_fields = ["Function", "File", "Line", "Folder"]
        d1 = exported_to_dict(in_file1, keep_fields)
        d2 = exported_to_dict(in_file2, keep_fields)
        result_dict = combine_dicts(d1, d2)
        write_dicts(keep_fields, result_dict, out_file)
        pass


def usage():
    """ Usage:
    python3 poly-func-analysis.py in1 in2 out

    Combine the function information from files

        in1 and in2

    and produces the following files out

    The files may be absolute or relative to the current directory.
    """
    print(usage.__doc__)
    sys.exit(1)


if __name__ == u'__main__':
    if len(sys.argv) != 4:
        usage()

    options = sys.argv[1:]
    (in1_arg, in2_arg, out_arg) = options

    print('Combining function results for Polyspace files\n')
    func_analysis = PolyFunc()
    func_analysis.do_function_analysis(in1_arg, in2_arg, out_arg)
    print('\ndone.\n')
