#!/bin/python3

"""
Scraps Markdown doc files from 'etcd website' repository into one markdown file neatly.
"""
import os
import sys
import pathlib
import tempfile
import pypandoc
import re
import pdfkit

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


def iterate_directory(dir_path, tmp_dir, section_number, section_separator):
    """
    Searches for md files recursively. Writes found files into `out_file`.
    :param dir_path: pathlib.Path object pointing to the directory
    :param tmp_dir: a temporary directory for TOCs and intermediate files
    :param section_number: a tuple of int to track the section number through subdirectories
    :param section_separator: a separator to be used between to md files
    :return: a list of md files to include into conversion
    """

    print(f'Entering dir "{dir_path}"')

    filepath_sequence = []
    toc = []
    subdirs = []
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

    tmp_md_file_kwargs = {"mode": 'r+t', "encoding": 'UTF8', "delete": False, "dir": tmp_dir}

    with tempfile.NamedTemporaryFile(**tmp_md_file_kwargs) as sep_file:
        sec_sep_filepath = sep_file.name
        sep_file.write(section_separator)

    # TOC
    with tempfile.NamedTemporaryFile(**tmp_md_file_kwargs) as header_file:
        header_file.write(f'# Section {".".join(map(str, section_number))} "{this_title or dir_path.name}"\n\n')
        if this_description:
            header_file.write(f'{this_description}\n\n')
        filepath_sequence += [header_file.name]

    toc.sort(key=lambda x: int(x[0] or 0))
    subdirs.sort(key=lambda x: int(x[0] or 0))

    if len(toc) > 0 or len(subdirs) > 0:
        with tempfile.NamedTemporaryFile(**tmp_md_file_kwargs) as toc_file:
            toc_file.write('## Content\n\n')
            for _, title, description, path in toc + subdirs:
                toc_file.write(f'* {title or str(path)} &mdash; {description or "subsection"}\n\n')
            filepath_sequence += [toc_file.name, sec_sep_filepath]

    # Section content
    # For unknown reasons, website's Markdown flavor uses '..' to point to the current directory.
    # It creates problem for strict Markdown parsers.
    # So I copy files and replace '..' with absolute file path in Markdown links.
    md_broken_link_pat = re.compile(r'\[([^\]]+?)\]\(\.\./(.+?)\)')
    md_replace_link_pat = f'[\g<1>]({dir_path}/\g<2>)'
    if len(toc) > 0:
        for _, title, description, md_file in toc:
            print(f'processing file "{md_file.name}"')
            with tempfile.NamedTemporaryFile(**tmp_md_file_kwargs) as title_file:
                title_file.write(f'# {title or str(md_file)}\n\n')
                filepath_sequence += [title_file.name]
            with tempfile.NamedTemporaryFile(**tmp_md_file_kwargs) as trg_file:
                trg_file.write(md_broken_link_pat.sub(md_replace_link_pat, md_file.read_text(encoding='UTF8')))
                filepath_sequence += [trg_file.name]
            filepath_sequence += [sec_sep_filepath]

    # Subsections content
    if len(subdirs) > 0:
        subsec_idx = 1
        for _, _, _, subdir_path in subdirs:
            filepath_sequence += iterate_directory(subdir_path, tmp_dir, (*section_number, subsec_idx),
                                                   section_separator)
            subsec_idx += 1

    # If no any content
    if len(toc) == 0 and len(subdirs) == 0:
        with tempfile.NamedTemporaryFile(**tmp_md_file_kwargs) as no_content_file:
            no_content_file.write('No content.')
            filepath_sequence += [no_content_file.name, sec_sep_filepath]

    return filepath_sequence


def __main__():
    orig_path = pathlib.Path(sys.argv[1])
    out_filepath = pathlib.Path(sys.argv[2])
    assert orig_path.exists()
    assert orig_path.is_dir()
    assert '.pdf' == out_filepath.name[-4:]

    with tempfile.TemporaryDirectory() as out_tmp_dir:
        # roll all md files into one
        filepath_list = iterate_directory(orig_path, out_tmp_dir, (1,), SECTION_SEPARATOR)
        # convert md to pdf
        with tempfile.NamedTemporaryFile(mode='w+t', encoding='UTF8', delete=False, suffix='.html',
                                         dir=out_tmp_dir) as html_file:
            # with open('/tmp/bar/foo.html', mode='w+t', encoding='UTF8') as html_file:
            html_filepath = html_file.name
            # html_filepath = '/tmp/bar/foo.html'
            print(f'Conversion to html "{html_filepath}"')
            pypandoc.convert_file(filepath_list, 'html', format='md', outputfile=html_filepath,
                                  extra_args=['--standalone'])
        if html_filepath:
            print(f'Conversion to pdf "{out_filepath}"')
            pdfkit_options = {
                'enable-local-file-access': None,
                'load-media-error-handling': 'skip',
                'load-error-handling': 'skip',
                'images': None
            }
            pdfkit.from_file(input=html_filepath, output_path=out_filepath, options=pdfkit_options)
            print('Done')


__main__()
