# py-utils
A collection of handy utilities written in Python.
Currently the following are available:

- digestDepends.py
  Process .d files as produced by using the -MMD option for gcc and
  use that to find the files that were referenced, i.e. all of the
  dependencies. The goal is to find all the files that are
  needed to build a product.

- factoroptions.py
  When Polyspace configures a project by observing a build script,
  the resulting configuration specifies the options and include
  paths separately for each individual file. But other tools,
  e.g. Astree, might not have that facility and one would like
  to know which files share common options and include paths.
  That is the purpose of this script which takes as input
  a Polyspace project.

- find-ambiguous.py
  The goal of this script (which appears not to have been completed)
  is to find files whose names appear in more than one place
  in a set of candidate directories.

- poly-export-diff.py
  This script compares the outputs of two Polyspace jobs and
  writes out three files, the hits only in the first,
  the hits only in the second, and the hits in both.

- poly-func-analysis.py
  This module combines the information on uncalled or unreached functions from
  Polyspace check output files.

- poly-func-diff.py
  Like poly-export-diff.py, but it compares the output of the
  poly-func-analysis.py. So it shows which functions
  changed status of being called or not.
