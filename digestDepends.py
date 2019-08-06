# Program to digest make depend files
import os
import re
from typing import Dict, List, Set
from collections import defaultdict

DirectoryName = str
FileName = str




def extract_includes_from_file(source: FileName) -> Set[str]:
    """ Return a set of relative filenames included by a given source file. """
    includes = set()
    prog = re.compile('#include *[<"]([^">]*)[">]')
    with open(source, 'r') as f:
        for line in f:
            match = prog.match(line)
            if match:
                item = match.group(1)
                includes.add(item)
            pass
        pass
    return includes


def extract_includes_from_files(sources: List[FileName]) -> List[str]:
    """ Union and sort all include files as specified in the #include directives. """
    all_includes = set()
    for source in sources:
        includes = extract_includes_from_file(source)
        if len(includes) > 0:
            all_includes = all_includes.union(includes)
    result = [include for include in all_includes]
    result.sort()
    return result


def get_how_included(includes: List[FileName]):
    """ Return a dictionary showing how each simple include file is referenced.

    :param includes: The list of includes to analyze. Each item will be a relative
    path, e.g. "x/y/z.h".
    :return: A dictionary where the keys are the simple filename of an include files,
    e.g. z.h, and the associated value is a set of the ways the include file is
    referenced, e.g. {"z.h", "x/y/z.h").
    """
    result = dict()
    for path in includes:
        simple = os.path.basename(path)
        if simple in result:
            old_paths = result[simple]
            old_paths.add(path)
        else:
            new_paths = {path}
            result[simple] = new_paths
    return result


def get_unused_files(all_source_files: List[FileName], used_files: List[FileName]) -> List[FileName]:
    """ Subtract used files from all files to give unused files. """
    used_set = {used for used in used_files}
    result = [f for f in all_source_files if not (f in used_set)]
    return result


def get_unique_directories(filelist: List[FileName],
                           how_included: Dict[FileName, Set[FileName]]) -> List[DirectoryName]:
    """ Return list of unique directories that contain the given files. """
    dirs = []
    for file in filelist:
        simple = os.path.basename(file)
        if simple in how_included:
            paths = how_included[simple]
            if len(paths) > 1:
                print("multiple paths")
            for path in paths:
                if file.endswith('/' + path):
                    ref_dir = file[0: len(file) - len(path) - 1]
                    dirs.append(ref_dir)
            pass
        else:
            dirs.append(os.path.dirname(file))
            pass

    unique_dirs = get_unique_list(dirs)
    return unique_dirs


def get_unique_list(items):
    """ Return a sorted de-duplicated list of items from input list.

    :type items: List(str)
    :param items: The input list of strings
    :return: Sorted list with duplicates removed
    """
    items.sort()
    result = []
    previous = ''
    for item in items:
        if item != previous:
            result.append(item)
            previous = item
    return result


def digest_depend_file(filename: FileName) -> List[FileName]:
    """ Return list or normalized files referenced in a .depend file.

    :param filename: Name of the .depend file.
    :return: List of normalized dependencies.
    """
    depend_dir = os.path.dirname(filename)
    referenced_files = []
    with open(filename, 'r') as f:
        num = 0
        for line in f:
            if num == 0:
                colon = line.find(":")
                line = line[colon + 1:]
            items = digest_line(line, depend_dir)
            referenced_files = referenced_files + items
            num = num + 1
            pass
        pass
    return referenced_files


def digest_line(line, depend_directory):
    """ Return a list of normalized dependencies mentioned on the given line.

    :param line: The line to digest
    :param depend_directory: directory to which relative files are relative
    :return: List of normalized dependency file names.
    """
    line = line.strip("\\\n")
    items = line.split()
    normedItems = []
    for item in items:
        normed = DigestDepends.normalize_file(item, depend_directory)
        normedItems.append(normed)
    return normedItems


def get_source_extensions(filelist: List[FileName]) -> Set[str]:
    """ Return set of extensions used for source files.

    But also include some we expect that might not be in the build
    """
    extensions = {".c", ".cc", ".cpp", ".h", ".hh"}
    for file in filelist:
        ext = os.path.splitext(file)[1]
        if ext != '':
            extensions.add(ext)
        # else:
            # print("No extension for " + file)
    return extensions


def filter_includes(all_includes: List[FileName], referenced_files: List[FileName]):
    """ Filter a  list of include items by removing those that do not appear in referenced files.

    :param all_includes: Include items to filter
    :param referenced_files: List of all files referenced by the build
    :return: The sublist of all_includes that are used.
    """
    max_components = 0
    for include in all_includes:
        components = include.split('/')
        num_components = len(components)
        if num_components > max_components:
            max_components = num_components

    # Make dictionary for faster checking
    filter_dict = defaultdict(set)
    for filename in referenced_files:
        components = filename.split('/')
        num_components = min(len(components), max_components)
        prefix = filename
        suffix = ""
        for i in range(0, num_components):
            base = os.path.basename(prefix)
            prefix = os.path.dirname(prefix)
            if suffix != '':
                suffix = os.path.join(base, suffix)
            else:
                suffix = base
            filter_dict[suffix].add(prefix)
    ambiguous_includes = set()
    result = []
    for include in all_includes:
        if include in filter_dict:
            result.append(include)
            prefixes = filter_dict[include]
            if len(prefixes) > 1:
                ambiguous_includes.add(include)
        else:
            print("include filtered out: " + include)
    return result



class DigestDepends:
    """ Digest .depend files"""

    def __init__(self, project_root_directory: DirectoryName, tag: str):
        """ Initialize a DigestDepends object.

        :param tag: String marking this configuration analyzed
        :param project_root_directory:
        """
        self.tag = tag
        self.project_root_directory = project_root_directory

    def get_depend_files(self) -> List[FileName]:
        """ Return a list of depend files under the specified directory tree.

        :return: List of names of .depend files.
        """
        file_iter = (os.path.join(root, f)
                     for root, _, files in os.walk(self.project_root_directory)
                     for f in files)
        depend_file_iter = (f for f in file_iter if os.path.splitext(f)[1] == '.depend')
        return [f for f in depend_file_iter]

    def get_source_files(self, extensions: Set[str]) -> List[FileName]:
        """ Return a list of source files with the given extensions. """
        file_iter = (os.path.join(root, f)
                     for root, _, files in os.walk(self.project_root_directory)
                     for f in files)
        depend_file_iter = (f for f in file_iter if os.path.splitext(f)[1] in extensions)
        length_root_dir: int = len(self.project_root_directory)
        source_files = [f[length_root_dir + 1:] for f in depend_file_iter]
        source_files.sort()
        return source_files

    @staticmethod
    def normalize_file(file, depend_directory):
        """ Normalize file by converting relative files to absolute

        :param file: File name to be normalized
        :param depend_directory: relative files are relative to this directory
        :return: Normalized file
        """
        #if file.find('/.') != -1:
        #    print("Found file with dot: " + file)  # To check for embedded . or ..

        if file[0] != '/':
            file = os.path.join(depend_directory, file)
        file = os.path.abspath(file)
        real_file = os.path.realpath(file)
        if real_file != file:
            file = real_file
        return file

    def get_unique_depend_files(self) -> List[FileName]:
        """ Return sorted list of unique files referenced in the dependency files found in the root_directory tree.

        :return: List of source and include files referenced in the .depend files.
        """
        depend_files = self.get_depend_files()
        digested_contents = []
        for file in depend_files:
            digested = digest_depend_file(file)
            digested_contents = digested_contents + digested
        unique_list = get_unique_list(digested_contents)
        return unique_list

    def separate_system_and_project_files(self, unique_list: List[FileName]):
        """ Return lists of system and project files from the combined list.

        Decides if a file is a project file based on whether its name starts with the project root.

        :param unique_list: List of file names of all dependent files.
        :return: project_files, system_files
        """
        project_files: List[FileName] = []
        system_files = []
        length_project_root_dir: int = len(self.project_root_directory)
        for file in unique_list:
            if file.startswith(self.project_root_directory):
                file = file[length_project_root_dir + 1:]
                project_files.append(file)
            else:
                system_files.append(file)
        return project_files, system_files

    def get_ambiguous_includes(
            self,
            all_includes: List[FileName],
            project_directories: List[DirectoryName],
            system_directories: List[DirectoryName]) -> List[List[FileName]]:
        """ Return a list of lists with one list for each ambiguous include.

        The first element of each list is an include item as enclosed in #include "item", or
        #include <item>. The remaining items in the list are possible paths that the item
        could include.

        :param all_includes: Items in #include directives
        :param project_directories: Project-root-relative include directories
        :param system_directories: Absolute system include directories
        :return: The list of lists where an item is included only if there is more than
        one resolution.
        """
        project_root = self.project_root_directory
        len_root = len(project_root)
        abs_project_directories = [os.path.join(project_root, proj_dir) for proj_dir in project_directories]
        all_include_directories = abs_project_directories + system_directories
        result = []
        for include in all_includes:
            resolutions = set()
            for inc_dir in all_include_directories:
                candidate = os.path.join(inc_dir, include)
                if os.path.isfile(candidate):
                    candidate = os.path.realpath(candidate)
                    if candidate.startswith(project_root):
                        candidate = candidate[len_root+1:]
                    resolutions.add(candidate)
            if len(resolutions) > 1:
                sublist = [include]
                resolutions_list = [r for r in resolutions]
                resolutions_list.sort()
                sublist = sublist + resolutions_list
                result.append(sublist)
            elif len(resolutions) == 0:
                print("Unresolved include: " + include)

        return result

    def write_lines_with_newline(self, destination_filename: FileName, lines: List[str]) -> None:
        """ Write lines to destination_filename appending a newline to each line. """
        with open(destination_filename + '-' + self.tag + ".txt", "w") as w:
            for line in lines:
                w.write(line + '\n')
        pass

    def process_depend_files(self) -> None:
        """ Main program for processing .depend files.

        The goal of the program is:
        - To find the set of include directories needed to build
        - To find unused source files to they can be deleted to avoid confusing
          analyses that do look at everything in the source directories.
        """
        referenced_files = self.get_unique_depend_files()
        extensions = get_source_extensions(referenced_files)
        all_includes = extract_includes_from_files(referenced_files)
        all_includes_filtered = filter_includes(all_includes, referenced_files)
        self.write_lines_with_newline("uniqued-includes", all_includes_filtered)
        how_included = get_how_included(all_includes_filtered)
        project_files, system_files = self.separate_system_and_project_files(referenced_files)
        project_includes = extract_includes_from_files(project_files)
        project_includes_filtered = filter_includes(project_includes, referenced_files)
        self.write_lines_with_newline("uniqued-project-includes", project_includes_filtered)
        system_includes = extract_includes_from_files(system_files)
        system_includes_filtered = filter_includes(system_includes, referenced_files)
        self.write_lines_with_newline("uniqued-system-includes", system_includes_filtered)
        # self.write_lines_with_newline("uniqued-depends", referenced_files)
        self.write_lines_with_newline("uniqued-projfiles", project_files)
        self.write_lines_with_newline("uniqued-systemfiles", system_files)
        project_directories = get_unique_directories(project_files, how_included)
        system_directories = get_unique_directories(system_files, how_included)
        all_directories = project_directories + system_directories
        ambiguous_includes = self.get_ambiguous_includes(all_includes_filtered,
                                                         project_directories, system_directories)
        ambiguous_strings = [str(item) for item in ambiguous_includes]
        self.write_lines_with_newline("uniqued-ambiguous", ambiguous_strings)
        self.write_lines_with_newline("uniqued-projdirs", project_directories)
        self.write_lines_with_newline("uniqued-sysdirs", system_directories)
        all_source_files = self.get_source_files(extensions)
        self.write_lines_with_newline("uniqued-all-sources", all_source_files)
        unused_files = get_unused_files(all_source_files, project_files)
        self.write_lines_with_newline("uniqued-unused-sources", unused_files)
        pass


if __name__ == u'__main__':
    print('Digesting dependency files\n')
    digester = DigestDepends(os.getcwd(), 'CPU_B')
    digester.process_depend_files()
    print('\ndone.\n')
