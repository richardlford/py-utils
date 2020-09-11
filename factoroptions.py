# Program to digest make depend files
import os
import re
import sys
from typing import Dict, List, Set
from collections import defaultdict

DirectoryName = str
FileName = str


def usage():
    print(""" Usage:
    python factoroptions.py input-options-filename
    """)
    sys.exit(1)


def get_includes(line: str) -> Set[str]:
    """ Return the set of Include options from the -options-for-sources line. """
    parts = line.split(";")
    # parts[0] has the -options-for-sources and the source file.
    includes = {part for part in parts
                if (part.startswith("-I ") and not part.startswith("-I /usr"))}
    return includes


def get_usr_includes(line: str) -> Set[str]:
    """ Return the set of Include options from the -options-for-sources line. """
    parts = line.split(";")
    # parts[0] has the -options-for-sources and the source file.
    includes = {part for part in parts if part.startswith("-I /usr")}
    return includes


def get_non_includes(line: str) -> Set[str]:
    """ Return the set of non-Include options from the -options-for-sources line. """
    parts = line.split(";")
    # parts[0] has the -options-for-sources and the source file.
    others = {part for part in parts[1:] if not part.startswith("-I ")}
    return others


class FactorOptions:
    """ Digest .depend files"""

    def __init__(self, input_filename):
        self.input_filename = input_filename
        self.output_filename = input_filename + ".factored"
        self.includes_filename = input_filename + ".includes"
        self.defines_filename = input_filename + ".defines"
        self.lines = self.read_input
        # Collect the -options-for-sources lines.
        self.ofs_lines = [line for line in self.lines if line.startswith("-options-for-sources ")]
        common_includes = get_includes(self.ofs_lines[0])
        common_usr_includes = get_usr_includes(self.ofs_lines[0])
        common_other = get_non_includes(self.ofs_lines[0])
        print(f"len(common_includes) = {len(common_includes)}")
        print(f"len(common_usr_includes) = {len(common_usr_includes)}")
        print(f"len(common_other) = {len(common_other)}")
        for i in range(1, len(self.ofs_lines)):
            this_includes = get_includes(self.ofs_lines[i])
            common_includes = common_includes.union(this_includes)
            print(f"len(common_includes) = {len(common_includes)}")
            this_usr_includes = get_usr_includes(self.ofs_lines[i])
            common_usr_includes = common_usr_includes.union(this_usr_includes)
            print(f"len(common_usr_includes) = {len(common_usr_includes)}")
            this_other = get_non_includes((self.ofs_lines[i]))
            common_other = common_other.union(this_other)
            print(f"len(common_other) = {len(common_other)}")

        self.common_includes = common_includes
        self.common_usr_includes = common_usr_includes
        self.common_other = common_other
        self.factored = self.compute_output()
        pass

    @property
    def read_input(self) -> List[str]:
        with open(self.input_filename, 'r') as f:
            lines = [line.strip("\\\n") for line in f]
            return lines

    def is_common(self, arg):
        if arg in self.common_includes:
            return True
        if arg in self.common_usr_includes:
            return True
        return arg in self.common_other

    def compute_new_ofs(self, ofs_index) -> str:
        line = self.ofs_lines[ofs_index]
        parts = line.split(";")
        args = []
        for i in range(1, len(parts)):
            arg = parts[i]
            if not self.is_common(arg):
                args.append(arg)
        if args:
            argstring = ';'.join(args)
            result = ':'.join([parts[0], argstring])
            return result
        return ''

    def get_common_usr_include_list(self) -> List[str]:
        # Preserve the order from the first.
        line = self.ofs_lines[0]
        parts = line.split(";")
        result = []
        for i in range(1, len(parts)):
            part = parts[i]
            if part in self.common_usr_includes:
                if os.path.isdir(part[3:]):
                    result.append(part)
                else:
                    print(part + " is not a directory")
        return result

    def compute_output(self) -> List[str]:
        factored_lines = []
        ofs_index = 0
        for line in self.lines:
            if line.startswith("-options-for-sources "):
                factored = self.compute_new_ofs(ofs_index)
                if factored:
                    factored_lines.append(factored)
                ofs_index += 1
                pass
            else:
                if ofs_index == len(self.ofs_lines):
                    # We have processed the last ofs line. Output common.
                    factored_lines += ["# Start of factored options"]
                    # First the non-/usr includes.
                    sorted_includes = [include for include in self.common_includes
                                       if os.path.isdir(include[3:])]
                    sorted_includes.sort()
                    factored_lines += sorted_includes
                    # Next the /usr includes.
                    factored_lines += self.get_common_usr_include_list()
                    # Now the others. Let's sort them too.
                    sorted_others = [other for other in self.common_other]
                    sorted_others.sort()
                    factored_lines += sorted_others
                    # increment ofs_index so we don't do this again.
                    ofs_index += 1
                    factored_lines += ["# End of factored options"]

                # One of the original lines.
                factored_lines.append(line)
                pass
        return factored_lines

    def output_factored(self):
        with open(self.output_filename, "w") as w:
            for line in self.factored:
                w.write(line + '\n')
        pass

    def output_defines(self):
        with open(self.defines_filename, "w") as w:
            for line in self.common_other:
                w.write(line + '\n')
        pass


    def output_includes(self):
        with open(self.includes_filename, "w") as w:
            for line in self.common_usr_includes:
                w.write(line + '\n')
            for line in self.common_includes:
                w.write(line + '\n')
        pass


if __name__ == u'__main__':
    print('Factoring PolySpace Code Prover options\n')
    options = sys.argv
    if len(sys.argv) != 2:
        usage()

    factor = FactorOptions(options[1])
    factor.output_factored()
    factor.output_defines()
    factor.output_includes()
    print('\ndone.\n')
