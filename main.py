#!python3

"""
Scraps Markdown doc files from 'etcd website' repository into one markdown file neatly.
"""

import sys
import pathlib

SECTION_SEPARATOR = '\n\n---\n\n'
INDEX_FILENAME = '_index.md'
MD_EXT = '.md'


def get_file_header(md_file_path):
    """
    Look for the meta information about the md file.
    :param md_file_path: sys.Path to the markdown file
    :return: a tuple of TOC weigh, toc title, file description
    """
    title, weight, desc = None, None, None
    with md_file_path.open(mode='r', encoding='UTF8') as md_file:
        while line := md_file.readline():
            line = line.strip()
            if 'title:' in line:
                title = line.strip()[6:].lstrip()
            elif 'weight:' in line:
                weight = line.strip()[7:].lstrip()
            elif 'description:' in line:
                desc = line.strip()[12:].lstrip()
            if title and weight and desc:
                break
    return weight, title, desc


def get_dir_header(dir_path):
    """
    Looks for index file and returns metadata from it.
    :param dir_path: sys.Path to the directory
    :return: a tuple of toc weight, title of the section, description
    """
    for child in dir_path.iterdir():
        if child.name == INDEX_FILENAME:
            return get_file_header(child)

    return None, None, None


def iterate_directory(dir_path, out_file, section_number, section_separator):
    """
    Searches for md files recursively. Writes found files into `out_file`.
    :param dir_path: pathlib.Path object pointing to the directory
    :param out_file: a writable filehandler
    :param section_number: a tuple of int to track the section number through subdirectories
    :param section_separator: a separator to be used between to md files
    :return: none
    """
    toc = list()
    subdirs = list()
    this_title, this_description = None, None
    for child in dir_path.iterdir():
        if child.is_dir():
            weight, title, description = get_dir_header(child)
            subdirs.append((weight, title, description, child))
        elif child.is_file() and child.name == INDEX_FILENAME:
            _, this_title, this_description = get_file_header(child)
        elif child.is_file() and child.name[-3:] == MD_EXT:
            weight, title, description = get_file_header(child)
            toc.append((weight, title, description, child))

    # TOC
    out_file.write(f'# Section {".".join(map(str, section_number))} "{this_title or str(dir_path)}"\n\n')
    if this_description:
        out_file.write(f'{this_description}\n\n')

    toc.sort(key=lambda x: int(x[0] or 0))
    subdirs.sort(key=lambda x: int(x[0] or 0))

    if len(toc) > 0 or len(subdirs) > 0:
        out_file.write('## Content\n\n')
        for _, title, description, path in toc + subdirs:
            out_file.write(f'* {title or str(path)} &mdash; {description or "subsection"}\n\n')
        out_file.write(section_separator)

    # Section content
    if len(toc) > 0:
        for _, title, description, md_file in toc:
            out_file.write(f'# {title or str(md_file)}\n\n')
            out_file.write(md_file.read_text(encoding='UTF8'))
            out_file.write(section_separator)

    # Subsections content
    if len(subdirs) > 0:
        subsec_idx = 1
        for _, _, _, subdir_path in subdirs:
            iterate_directory(subdir_path, out_file, (*section_number, subsec_idx), section_separator)
            subsec_idx += 1

    # If no any content
    if len(toc) == 0 and len(subdirs) == 0:
        out_file.write('No content.')
        out_file.write(section_separator)


def __main__():
    orig_path = pathlib.Path(sys.argv[1])
    out_filepath = pathlib.Path(sys.argv[2])
    assert orig_path.exists() and orig_path.is_dir()

    with out_filepath.open(mode='w', encoding='UTF8') as out_file:
        iterate_directory(orig_path, out_file, (1,), SECTION_SEPARATOR)


__main__()
