import os
import re
import argparse
from difflib import SequenceMatcher
from pathlib import Path


def get_includes_from_shader(c_file_path):
    included_files = []
    include_pattern = r'#\s*include\s*["<](.+?)[">]'
    single_line_comment_pattern = r'\/\/.*?$'
    multi_line_comment_pattern = r'\/\*.*?\*\/'

    with open(c_file_path, 'r') as file:
        content = file.read()

        # Remove single-line comments
        content = re.sub(single_line_comment_pattern,
                         '', content, flags=re.MULTILINE)

        # Remove multi-line comments
        content = re.sub(multi_line_comment_pattern,
                         '', content, flags=re.DOTALL)

        # Find all include statements using regular expressions
        matches = re.findall(include_pattern, content)

        # Process each match and add the included file paths to the list
        for match in matches:
            included_files.append(match)

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


def crawl_and_verify(directory_path):
    all_files = []
    all_includes = {}

    # In a first pass, collects all file paths and all includes.
    for directory, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.normpath(os.path.join(directory, file))
            all_files.append(os.path.relpath(file_path, directory_path))
            _, ext = os.path.splitext(file)
            if ext in ['.glsl', '.slang']:
                includes = get_includes_from_shader(file_path)
                all_includes[file_path] = []
                for include in includes:
                    include_path = os.path.join(directory, include)
                    all_includes[file_path].append(
                        os.path.normpath(include_path))

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
