# Program to digest make depend files
import os
from typing import List, Set

DirectoryName = str
FileName = str


def get_unused_files(all_source_files: List[FileName], used_files: List[FileName]) -> List[FileName]:
    """ Subtract used files from all files to give unused files. """
    used_set = {used for used in used_files}
    result = [f for f in all_source_files if not (f in used_set)]
    return result


def get_unique_directories(filelist: List[FileName]) -> List[DirectoryName]:
    """ Return list of unique directories that contain the given files. """
    dirs = [os.path.dirname(file) for file in filelist]
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
    """ Return set of extensions used for source files. """
    extensions = set()
    for file in filelist:
        ext = os.path.splitext(file)[1]
        if ext != '':
            extensions.add(ext)
        else:
            pass
    return extensions


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
        if file.find('.'):
            pass  # To check for embedded . or ..

        if file[0] != '/':
            file = os.path.join(depend_directory, file)
        file = os.path.abspath(file)
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
        project_files, system_files = self.separate_system_and_project_files(referenced_files)
        # self.write_lines_with_newline("uniqued-depends", referenced_files)
        self.write_lines_with_newline("uniqued-projfiles", project_files)
        self.write_lines_with_newline("uniqued-systemfiles", system_files)
        project_directories = get_unique_directories(project_files)
        system_directories = get_unique_directories(system_files)
        self.write_lines_with_newline("uniqued-projdirs", project_directories)
        self.write_lines_with_newline("uniqued-sysdirs", system_directories)
        all_source_files = self.get_source_files(extensions)
        self.write_lines_with_newline("uniqued-all-sources", all_source_files)
        unused_files = get_unused_files(all_source_files, project_files)
        self.write_lines_with_newline("uniqued-unused-sources", unused_files)
        pass


if __name__ == u'__main__':
    print('Digesting dependency files\n')
    digester = DigestDepends(os.getcwd(), 'CPU_A')
    digester.process_depend_files()
    print('\ndone.\n')
