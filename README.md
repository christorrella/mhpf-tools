# mhpf-tools
package tools for the "Melbourne House Pack File" file format (.PCK)

it's messy for now, but it works.

usage:

mhpf-tools.py -u/-p/-s (--unpack/--pack/--scan) -i (--input) <input file/dir> -o (--output) <output file/dir>

"unpack" mode takes .pck file as input, creates output directory

"pack" mode takes directory as input, creates output pack file

"scan" mode takes .pck file as input, prints information about given pack file
