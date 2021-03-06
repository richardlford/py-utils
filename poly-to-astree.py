"""
This module reads a Polyspace options file (that was generated by watching a build)
and generates an Astree configuration dax fragment.
"""
import os
import re
import sys
from typing import Dict, List, Set, FrozenSet
from collections import defaultdict

DirectoryName = str
FileName = str


def get_includes(line: str) -> Set[str]:
    """ Return the set of Include options from the -options-for-sources line. """
    parts = line.split(";")
    # parts[0] has the -options-for-sources and the source file.
    includes = {part for part in parts
                if (part.startswith("-I ") and not part.startswith("-I /usr"))}
    return includes


def partition_parts(part_dict: Dict[str, List[str]]) -> List[Set[str]]:
    part_keys = list(part_dict)
    num_keys = len(part_keys)
    assert (num_keys > 0)
    first_key = part_keys[0]
    first_list = part_dict[first_key]
    first_set = set(first_list)
    partition = [first_set]
    all_parts = set()
    for i in range(1, num_keys):
        for pi in partition:
            if len(pi) == 0:
                assert (False)
        parts = set(part_dict[part_keys[i]])
        all_parts.update(parts)
        new_partition = []
        for pi in partition:
            if len(parts) == 0:
                new_partition.append(pi)
            elif parts.isdisjoint(pi):
                new_partition.append(pi)
            elif parts == pi:
                new_partition.append(pi)
                parts = set()
            else:
                inter = parts.intersection(pi)
                dif = pi.difference(parts)
                parts = parts.difference(pi)
                new_partition.append(inter)
                if len(dif) > 0:
                    new_partition.append(dif)
                pass
            pass
        if len(parts) > 0:
            new_partition.append(parts)
        partition = new_partition
        pass
    pass
    partition = sorted(partition, key=len, reverse=True)
    partition_all = set();
    for pi in partition:
        partition_all.update(pi)
    assert (all_parts == partition_all)
    for i in range(len(partition)):
        for k in range(i + 1, len(partition)):
            assert (partition[i].isdisjoint(partition[k]))
    return partition


def get_file_partition_indices(part_dict: Dict[FileName, List[str]], partition) -> Dict[FileName, List[int]]:
    result = {}
    for file in part_dict:
        parts = part_dict[file]
        part_set = set(parts)
        file_result = []
        result[file] = file_result
        for i in range(len(partition)):
            parti = partition[i]
            if parti <= part_set:
                file_result.append(i)
        pass
    return result


def get_index_groups(file_indices: Dict[FileName, List[int]]) -> Dict[FrozenSet[int], List[FileName]]:
    """
    The range of file_indices is a list of indices into the partition of options/definitions, etc.
    Call these option partition groups.

    Results returned:

    group_list - a list of frozen groups, sorted by descending frequency of use.

    """

    #
    group_to_file_list_dict: Dict[FrozenSet[int], List[FileName]] = {}
    for file in list(file_indices):
        indices = frozenset(file_indices[file])
        if indices in group_to_file_list_dict:
            group_to_file_list_dict[indices].append(file)
        else:
            group_to_file_list_dict[indices] = [file]
    group_list = sorted(list(group_to_file_list_dict), key=lambda fset: len(group_to_file_list_dict[fset]),
                        reverse=True);
    group_indices = dict([[group_list[i], i] for i in range(len(group_list))])
    group_index_to_files = dict([[group_indices[fset], group_to_file_list_dict[fset]] for fset in group_list])
    file_group = dict([[file, group_indices[frozenset(file_indices[file])]] for file in list(file_indices)])
    group_index_to_dirs = dict(
        [[fset_index, set([os.path.dirname(file) for file in group_index_to_files[fset_index]])] for fset_index in
         group_index_to_files])
    # Get which group indices a directory is in. We fill in with empty lists so the
    # dictionary will be in alphabetical order (because the files are).
    dir_groups: Dict[DirectoryName, List[int]] = dict([[os.path.dirname(file), []] for file in list(file_indices)])

    for fset_index in list(group_index_to_dirs):
        dirs = group_index_to_dirs[fset_index]
        for dir in dirs:
            dir_groups[dir].append(fset_index)
    return (group_list, group_index_to_files, file_group, group_index_to_dirs, dir_groups)


def strip_leading(arg: str, leading: str):
    if arg.startswith(leading):
        return "./" + arg[len(leading):]
    else:
        return arg


class AstreeConfigure:
    """ Digest .depend files"""

    def adjust_src(self, arg: str):
        for old in list(self.adjust_dict):
            if arg.startswith(old):
                return self.adjust_dict[old] + arg[len(old):]
        return arg

    def old_to_new(self, arg: str):
        for old in list(self.old_to_new_dict):
            if arg.startswith(old):
                return self.old_to_new_dict[old] + arg[len(old):]
            elif arg.startswith('"' + old):
                return '"' + self.old_to_new_dict[old] + arg[len(old)+1:]
        return arg

    def expand_symbolic_src(self, arg: str):
        for symbolic_ref in list(self.symbol_dict):
            if arg.startswith(symbolic_ref):
                result = self.symbol_dict[symbolic_ref] + arg[len(symbolic_ref):]
                return result
        return arg

    def strip_inc(self, arg: str):
        if arg.startswith('-I '):
            return '-I ' + self.adjust_src(arg[3:])
        else:
            return arg

    def normalize_dir(self, the_dir: DirectoryName):
        if not the_dir.endswith("/"):
            return the_dir + "/"
        else:
            return the_dir

    def get_vocabulary(self) -> List[str]:
        result: Set[str] = set()
        for file in list(self.ofs_dict):
            values = self.ofs_dict[file]
            for value in values:
                result.add(value)
        result_list1 = list(result)
        result_list2 = sorted(result_list1)
        return result_list2

    def filter_vocabulary(self):
        """
        Remove specifications we think will cause problems.
        """
        filter_set = set();
        for value in self.vocabulary:
            v: str = value
            if v.startswith('-D _'):
                filter_set.add(v)
            elif v.startswith('-I /usr'):
                filter_set.add(v)
            elif v.startswith('-D BIG'):
                filter_set.add(v)
            # elif v.startswith('-D CPU'):
            #    filter_set.add(v)
            elif v.startswith('-D NRTSIM'):
                filter_set.add(v)
            elif v.startswith('-D TARGET_CPU'):
                filter_set.add(v)
            elif v.startswith('-D i386'):
                filter_set.add(v)
            # elif v.startswith('-c-version'):
            #     filter_set.add(v)
            # elif v.startswith('-cpp-version '):
            #     filter_set.add(v)
            elif not v.startswith('-lang ') and not v.startswith("-I ") \
                    and not v.startswith("-D "):
                filter_set.add(v)

        # Allow some others

        filter_list = list(filter_set)
        remnant = set(self.vocabulary) - filter_set
        sorted_remnant = sorted(list(remnant))
        defines = [value for value in sorted_remnant if value.startswith('-D ')]
        includes = [value for value in sorted_remnant if value.startswith('-I ')]
        other = [value for value in sorted_remnant if not value.startswith('-I ') and not value.startswith('-D ')]

        # Now edit the ofs_dict removing the filtered items.
        for file in list(self.ofs_dict):
            old_items = self.ofs_dict[file]
            new_items = [item for item in old_items if not item in filter_set]
            self.ofs_dict[file] = new_items
            pass

        # Now for some kludges.

        print("Done filtering")

    def __init__(self, input_filename: FileName, output_filename: FileName, triples: List[str]):
        # Amount to indent xml per level
        self.indent = "    "
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.adjust_dict = {}
        self.symbol_dict = {}
        self.old_to_new_dict = {}
        for i, triple in enumerate(triples):
            old, symbol, new = triple.split(';')
            old = self.normalize_dir(old)
            new = self.normalize_dir(new)
            symbol_ref = '${' + symbol + "}"
            self.adjust_dict[old] = symbol_ref + '/'
            self.symbol_dict[symbol_ref] = new[:-1]
            self.old_to_new_dict[old] = new

        self.lines = self.read_input
        # Collect the -options-for-sources lines.
        self.ofs_lines = [line[len("-options-for-sources "):]
                          for line in self.lines if line.startswith("-options-for-sources ")]
        ofs_dict0 = dict([[self.adjust_src(line.split(";")[0]),
                           [self.strip_inc(option) for option in line.split(";")[1:]]]
                          for line in self.ofs_lines])
        # Get ofs_dict in sorted order.
        self.filenames = sorted(ofs_dict0.keys())
        self.ofs_dict = dict([[file, ofs_dict0[file]] for file in self.filenames])
        self.vocabulary = self.get_vocabulary()
        # self.filter_vocabulary()
        self.partition = partition_parts(self.ofs_dict)
        self.indices_dict = get_file_partition_indices(self.ofs_dict, self.partition)
        self.group_list, self.group_index_to_files, self.file_group, self.group_index_to_dirs, self.dir_groups = \
            get_index_groups(self.indices_dict)

        # common_includes = get_includes(self.ofs_lines[0])
        # common_usr_includes = get_usr_includes(self.ofs_lines[0])
        # common_other = get_non_includes(self.ofs_lines[0])
        # print(f"len(common_includes) = {len(common_includes)}")
        # print(f"len(common_usr_includes) = {len(common_usr_includes)}")
        # print(f"len(common_other) = {len(common_other)}")
        # includes_list = []
        # usr_includes_list = []
        # other_list = []
        # for i in range(1, len(self.ofs_lines)):
        #     this_includes = get_includes(self.ofs_lines[i])
        #     includes_list.append(this_includes)
        #     common_includes = common_includes.intersection(this_includes)
        #     print(f"len(common_includes) = {len(common_includes)}")
        #     this_usr_includes = get_usr_includes(self.ofs_lines[i])
        #     usr_includes_list.append(this_usr_includes)
        #     common_usr_includes = common_usr_includes.intersection(this_usr_includes)
        #     print(f"len(common_usr_includes) = {len(common_usr_includes)}")
        #     this_other = get_non_includes((self.ofs_lines[i]))
        #     other_list.append(this_other)
        #     common_other = common_other.intersection(this_other)
        #     print(f"len(common_other) = {len(common_other)}")
        #
        # self.common_includes = common_includes
        # self.common_usr_includes = common_usr_includes
        # self.common_other = common_other
        # self.factored = self.compute_output()
        pass

    @property
    def read_input(self) -> List[str]:
        with open(self.input_filename, 'r') as f:
            lines = [line.strip("\\\n") for line in f]
            return lines

    def relative_path(self, the_path: str, the_dir: DirectoryName):
        if the_path.startswith(the_dir):
            if len(the_path) > len(the_dir):
                result = the_path[len(the_dir) + 1:]
            else:
                result = the_path
        else:
            result = the_path
        return result

    def get_group_properties(self, group: int) -> Set[str]:
        group_partition_indices = self.group_list[group]
        result = set()
        for part_index in group_partition_indices:
            part_set = self.partition[part_index]
            result.update(part_set)
        return result

    def get_includes_for_group(self, libname: str, group: int):
        group_properties: Set[str] = self.get_group_properties(group)

        # For includes, the order may be important. Use the order of the
        # first file for this group.
        first_file = self.group_index_to_files[group][0]
        file_props: List[str] = self.ofs_dict[first_file]
        include_list = []
        for prop in file_props:
            assert (prop in group_properties)
            if prop.startswith('-I '):
                include_list.append(self.expand_symbolic_src(prop[3:]))

        return include_list

    def get_defines_for_group(self, libname: str, group: int):
        group_properties: Set[str] = self.get_group_properties(group)

        # For defines, the order is not important, but use the order of the
        # first file for this group anyway.
        first_file = self.group_index_to_files[group][0]
        file_props: List[str] = self.ofs_dict[first_file]
        define_set = set()
        for prop in file_props:
            assert (prop in group_properties)
            if prop.startswith('-D '):
                old_def = prop[3:]
                def_parts = old_def.split("=")
                if len(def_parts) == 2:
                    new_rhs = self.old_to_new(def_parts[1])
                    def_parts[1] = new_rhs
                    old_def = "=".join(def_parts)
                define_set.add(old_def)

        define_list = list(define_set)
        define_list = sorted(define_list)

        # For defines with value, check no duplicates.
        dup_dict = {}
        for define in define_list:
            parts = define.split("=")
            assert (len(parts) <= 2)
            if len(parts) == 2:
                lhs = parts[0]
                if lhs in dup_dict:
                    print(f"Duplicate define: new={define}, previous='{lhs}={dup_dict[lhs]}'")
                else:
                    dup_dict[lhs] = parts[1]

        return define_list

    def get_options_for_group(self, libname: str, group: int):
        group_properties: Set[str] = self.get_group_properties(group)

        # For options, the order is not important, but use the order of the
        # first file for this group anyway.
        first_file = self.group_index_to_files[group][0]
        file_props: List[str] = self.ofs_dict[first_file]
        option_set = set()
        for prop in file_props:
            assert (prop in group_properties)
            if not prop.startswith('-D ') and not prop.startswith('-I '):
                option_set.add(prop)

        option_list = list(option_set)
        option_list = sorted(option_list)

        return option_list

    def get_config_for_group_and_dir(self, the_dir: DirectoryName, group: int):
        config = {}
        # Use the first source file for the name of the library.
        group_dir_file_list = [file for file in self.group_index_to_files[group] if os.path.dirname(file) == the_dir]

        assert (len(group_dir_file_list) > 0)
        parts = the_dir.split("/")
        if len(self.dir_groups[the_dir]) > 1 or len(parts) == 1:
            # This directory uses more than one group, so base library name on first file
            first_file = group_dir_file_list[0]
            first_without_ext = os.path.splitext(first_file)[0]
            parts = first_without_ext.split('/')

        if 'src' in parts:
            parts.remove('src')
        libname = "_".join(parts[1:])
        config['name'] = libname
        config['base'] = self.expand_symbolic_src(the_dir)
        files = []
        languages = set()
        language = ''
        for file in group_dir_file_list:
            relative_file = self.relative_path(file, the_dir)
            ext = os.path.splitext(relative_file)[1]
            if ext == '.cc':
                language = 'C++'
            elif ext == '.c':
                language = 'C'
            else:
                print(f"Unrecognized extension: {ext}")
            languages.add(language)

            files.append(relative_file)
        if len(languages) != 1:
            print("Mixed languages")
        else:
            config['language'] = language

        config['files'] = files

        includes = self.get_includes_for_group(libname, group)
        config['includes'] = includes
        defines = self.get_defines_for_group(libname, group)
        config['defines'] = defines
        options = self.get_options_for_group(libname, group)
        if len(options) > 0:
            print("Have options")

        # Astree does not have compiler options in configurations
        return config

    def output_single(self, config, key: str, val: str):
        self.addline(f"<{key}>{val}</{key}>")
        pass

    def output_list(self, config, key: str):
        ekey = key[:-1]
        self.addline(f"<{key}>")
        self.level += 1
        for elem in config[key]:
            self.output_single(config, ekey, elem)
        self.level -= 1
        self.addline(f"</{key}>")
        pass

    def output_config(self, config):
        self.addline(f"<config name=\"{config['name']}\">")
        self.level += 1
        self.output_single(config, 'base', config['base'])
        self.output_single(config, 'language', config['language'])
        self.output_list(config, 'files')
        self.output_list(config, 'includes')
        self.output_list(config, 'defines')
        self.level -= 1
        self.addline(f"</config>")
        pass

    def addline(self, line):
        self.w.write(self.indent * self.level)
        self.w.write(line)
        self.w.write("\n")

    def output_astree_config(self):
        configs = []
        for the_dir in list(self.dir_groups):
            for group in self.dir_groups[the_dir]:
                config = self.get_config_for_group_and_dir(the_dir, group)
                configs.append(config)

        with open(self.output_filename, "w") as w:
            self.w = w
            self.level = 0
            self.addline("""<?xml version="1.0" encoding="utf-8"?>
<dax mode="astree" comment-mode="AAL" version="1.9" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.absint.com/dtd/a3-dax-20.04.xsd" xmlns="http://www.absint.com/dax">
    <preprocess>
        <config name="TopConfig">""")
            self.level = 3
            for config in configs:
                self.output_config(config)
            self.level = 0
            self.addline("""        </config>
    </preprocess>
</dax>""")
            pass
        print("Done writing")


def usage():
    """ Usage:
    python3 poly-to-astree.py  output_file  poly_options_file [triple]...

    Write Astree configuration dax fragment for a project that has previously
    been configured for Polyspace.

    poly_options_file is the path to a Polyspace options file
    that contains the compilation options for each file of the project.

    output_file is the dax fragment to be inserted into an Astree Dax file.

    The triples are strings of the form "old;symbolic;new"
    where
      "old" is a path on the system where Polyspace was run,
      "symbolic" is a variable name that will be used the astreeLists.txt files
         to represent that directory.
      "new" is a path to the corresponding directory on the current machine

    The triples are optional
    """
    print(usage.__doc__)
    sys.exit(1)


if __name__ == u'__main__':
    print('Using PolySpace Code Prover options to produce Astree configuration\n')
    options = sys.argv[1:]
    if len(options) < 2:
        usage()
    triples = options[2:]
    for triple in triples:
        if len(triple.split(';')) != 3:
            usage()

    config = AstreeConfigure(options[0], options[1], triples)
    config.output_astree_config()
    print('\ndone.\n')
