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


def exported1_to_dict(filename: FileName, key_fields: List) -> (Dict, List):
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
            line = line.strip("\\\n")
            fields = line.split('\t')
            if fields[0].strip(' ') == '':
                continue
            num = num + 1
            if num == 1:
                keys = fields
                keysSet = set(keys)
                for k in key_fields:
                    if k != 'Line' and k not in keysSet:
                        print(f'key {k} in not in the keysSet')
                continue
            entry = {}
            for i in range(len(keys)):
                if i < len(fields):
                    entry[keys[i]] = fields[i]
                else:
                    entry[keys[i]] = ''
                pass
            # Keep the Location field for use in outputting non-matches.
            location_fields = entry['Location'].split(':')
            path = location_fields[0]
            directory = os.path.dirname(path)
            file = os.path.basename(path)
            entry['Folder'] = directory
            entry['File'] = file
            entry['Line'] = location_fields[1].strip(' ')
            keyfieldValues = [entry[k] for k in key_fields]
            entryKey = '\t'.join(keyfieldValues)
            if entryKey in result_dict:
                existing_entry = result_dict[entryKey]
                print(f"Ambiguous data for key={entryKey}, \n    existing={existing_entry}\n    new={entry}\n")
            else:
                result_dict[entryKey] = entry
            pass

    return result_dict, keys

def exported2_to_dict(filename: FileName, key_fields: List) -> (Dict, List):
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
            line = line.strip("\\\n")
            fields = line.split('\t')
            if fields[0].strip(' ') == '':
                continue
            num = num + 1
            if num == 1:
                keys = fields
                keysSet = set(keys)
                for k in key_fields:
                    if k != 'Location' and k not in keysSet:
                        print(f'key {k} in not in the keysSet')
                continue
            entry = {}
            for i in range(len(keys)):
                if i < len(fields):
                    entry[keys[i]] = fields[i]
                else:
                    entry[keys[i]] = ''

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

def merge_dictionaries(d1: Dict, d2: Dict, inboth: List):
    for k in inboth:
        entry1 = d1[k]
        entry2 = d2[k]
        for key in entry1.keys():
            if key not in entry2:
                entry2[key] = entry1[key]
    pass


""" Write dictionary to file.
"""


def write_dicts(field_keys: List, caption_keys: List, entry_keys: List, d: Dict, filename: FileName):
    """
    Write the specified fields of a specified entries of a dictionary of dictionaries to file.

    :param d: The input dictionary of dictionaries.
    :param entry_keys: A list of keys of d whose corresponding dictionaries are to be output.
    :param field_keys: The fields of the inner dictionaries that are to be output (in the given order).
    :param caption_keys: The names of the fields that are to appear in the header. This allows the
    fields to have different names externally than internally.
    :param filename: The name of the file that is to be written.
    :return: Nothing
    """
    with open(filename, "w") as w:
        line = "\t".join(caption_keys)
        w.write(line + '\n')
        for entryKey in entry_keys:
            entry = d[entryKey]
            fields = []
            for key in field_keys:
                if key in entry:
                    field = entry[key]
                else:
                    field = ''
                fields.append(field)
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


    def do_diff2(self, input_file1: FileName, input_file2: FileName, merge_file: FileName):
        """
        Compute and output the differences between two Polyspace check files.

        :param input_file1: Path holding the first file.
        :param input_file2: Path holding the second file.
        :param merge_file: Result file
        :return: None, but output is written into files.
        """
        fullFile1 = input_file1
        fullFile2 = input_file2
        merge_dir = os.path.dirname(merge_file)
        os.makedirs(merge_dir, exist_ok=True)
        out_root = os.path.splitext(merge_file)[0]
        d1only_file = out_root + ".d1only.txt"
        keyFields = ["Family", "File", "Line", "Col", "Folder", "Class", "Function", "Detail"]
        d1, d1FieldKeys = exported1_to_dict(fullFile1, keyFields)
        d2, d2FieldKeys = exported2_to_dict(fullFile2, keyFields)
        # assert (d1FieldKeys == d2FieldKeys)
        d1OnlyKeys, d2OnlyKeys, inBothKeys = compare_dicts(d1, d2)
        merge_dictionaries(d1, d2, inBothKeys)
        output_field_keys = d2FieldKeys.copy()
        caption_keys = d2FieldKeys.copy()
        output_field_keys.append('1st Analyst')
        caption_keys.append('1.4 Analyst')
        output_field_keys.append('1st Status')
        caption_keys.append('1.4 Status')
        output_field_keys.append('1st Criticality')
        caption_keys.append('1.4 Criticality')
        output_field_keys.append('1st Rationale')
        caption_keys.append('1.4 Rationale')
        write_dicts(output_field_keys, caption_keys, d2.keys(), d2, merge_file)
        write_dicts(d1FieldKeys, d1FieldKeys, d1OnlyKeys, d1, d1only_file)
        pass


def usage():
    """ Usage:
    python3 poly-export-diff.py input_file1 input_file2 merged_root.txt

    Compares the contents of Polyspace output files

        ./dir1/file_root and ./dir2/file_root

    and produces the following files

        merged_root-d1only.txt
        merged_root.txt

    where root is file_root with its file extension removed.
    The output files are in the same format as the input files,
    i.e. tab-separated fields with the first line containing
    the field keys.
    """
    print(usage.__doc__)
    sys.exit(1)


if __name__ == u'__main__':
    if len(sys.argv) != 4:
        usage()

    options = sys.argv[1:]
    (input_file1_arg, input_file2_arg, merge_file) = options

    print('Finding differences in Polyspace result export files\n')
    differ = PolyDiff(os.getcwd())
    differ.do_diff2(input_file1_arg, input_file2_arg, merge_file)
    print('\ndone.\n')
