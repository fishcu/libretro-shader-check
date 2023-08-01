import os
import re
import argparse
from difflib import SequenceMatcher
from pathlib import Path
from collections import defaultdict


def get_includes_from_shader(file_path):
    # Loads a file, then strips all comments before
    # finding all includes.
    included_files = []
    include_pattern = r'#\s*include\s*["<](.+?)[">]'
    single_line_comment_pattern = r'\/\/.*?$'
    multi_line_comment_pattern = r'\/\*.*?\*\/'

    try:
        with open(file_path, 'r') as file:
            content = file.read()
            content = re.sub(single_line_comment_pattern,
                             '', content, flags=re.MULTILINE)
            content = re.sub(multi_line_comment_pattern,
                             '', content, flags=re.DOTALL)
            matches = re.findall(include_pattern, content)
            for match in matches:
                included_files.append(match)
    except Exception as e:
        print(f"Error processing file {file_path}: ", e)

    return included_files


def find_similar_include(original_include, all_files):
    # Finds the most similar include fill in the list of all files.
    # Only considers files that match the exact file name,
    # and then uses a heuristic similarity measure to find the best match.
    include_file = os.path.basename(original_include)
    max_similarity = 0
    suggested_include = None

    for file in all_files:
        if include_file == os.path.basename(file):
            similarity_ratio = SequenceMatcher(
                None, original_include, file).ratio()
            if similarity_ratio > max_similarity:
                max_similarity = similarity_ratio
                suggested_include = file
    return suggested_include


def _count_file_extensions(file_paths):
    extension_counts = defaultdict(int)

    for file_path in file_paths:
        _, extension = os.path.splitext(file_path)
        extension_counts[extension] += 1

    sorted_counts = sorted(extension_counts.items(),
                           key=lambda item: item[1], reverse=True)

    for extension, count in sorted_counts:
        print(f"{extension}: {count}")


def crawl_and_verify(crawl_path):
    source_code_extensions = ['.glsl', '.slang', '.h', '.inc', '.params', '.hlsl']
    # preset_extensions = ['.glslp', '.slangp']
    all_files = []
    all_includes = {}

    # In a first pass, collects all file paths and all includes.
    for directory, _, files in os.walk(crawl_path):
        # Skip .git and similar folders
        parts = directory.split(os.path.sep)
        if any(part.startswith(".") for part in parts):
            continue
        for file in files:
            file_path = os.path.relpath(os.path.normpath(
                os.path.join(directory, file)), crawl_path)
            all_files.append(file_path)
            _, ext = os.path.splitext(file)
            # if len(ext) == 0:
            #     print(f"file without file ending: {file_path}")
            if ext in source_code_extensions:
                includes = get_includes_from_shader(
                    os.path.join(directory, file))
                all_includes[file_path] = []
                for include in includes:
                    all_includes[file_path].append(
                        os.path.relpath(
                            os.path.normpath(
                                os.path.join(directory, include)),
                            crawl_path))

    # print(all_files)
    # print(all_includes)
    # _count_file_extensions(all_files)

    # In a second pass, verifies all includes.
    # If a file is missing, a suggested replacement is searched for.
    for file_path, includes in all_includes.items():
        missing_includes = [x for x in includes if x not in all_files]
        if len(missing_includes):
            print(f"Missing includes in {file_path}:")
        for missing_include in missing_includes:
            print(f"\t{missing_include}")
            suggested_include = find_similar_include(
                missing_include, all_files)
            if suggested_include:
                suggested_rel_path = os.path.relpath(
                    suggested_include, os.path.dirname(file_path))
                print(
                    f"\t\tSuggested include path: {Path(suggested_rel_path).as_posix()}")
            else:
                print("\t\tNo suggestions found.")


def main():
    parser = argparse.ArgumentParser(
        description='Verify and suggest missing include paths in shader and preset files.')
    parser.add_argument('directory_path', type=str,
                        help='The path to the directory to crawl and verify.')

    args = parser.parse_args()
    directory_path = args.directory_path

    if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
        print(f"Error: '{directory_path}' is not a valid directory path.")
        return

    crawl_and_verify(directory_path)


if __name__ == '__main__':
    main()
