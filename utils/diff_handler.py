import difflib


def get_difference(s1, s2):
    """
    Using difflib, returns a list of strings with the differences between s1 and s2.
    Adding a '+' in front of the string means it's an addition.
    Subtracting a '-' in front of the string means it's a deletion.
    ? means it's a change that is not an addition or deletion.
    """
    diff = difflib.Differ()
    difference = list(diff.compare(s1.split(), s2.split()))
    return difference


def create_color_indexes(diff):
    """
    Creates a list of tuples with the start and end index of the additions in the diff list.

    1. Loop through the difference list.
    2. If it's just a normal piece of text, add length of the string to index tracker.
    3. If it is an addition, get the a start and end index.
    We do this by:
        A. getting the latest number of the index tracker.
        B. start = index_tracker+1, end = index_tracker +1 - length(string) -1.
        C. add lenght(string) - 1 to index tracker.

    """
    index_tracker = -1
    indexes = []
    for word in diff:
        if word.startswith("+"):
            start_index = index_tracker + 1
            end_index = start_index + len(word) - 1
            indexes.append((start_index, end_index))
            index_tracker += len(word) - 1
        elif word.startswith("-"):
            continue
        elif word.startswith("?"):
            continue
        else:
            index_tracker += len(word) - 1
    return indexes


def diff_to_html(diff):
    """
    Returns a string of html with the differences between s1 and s2.
    Adds green color to additions and strikethrough to deletions.
    """
    markdown = ""
    for line in diff:
        if line.startswith("+"):
            markdown += f"<span style='color:green'>{line[1:]}</span>"
        elif line.startswith("-"):
            markdown += f"<s>{line[1:]}</s>"
        elif line.startswith("?"):
            continue
        else:
            markdown += f"{line}"

    html_start = (
        '<meta http-equiv="Content-Type" content="text/html; charset=utf-8"><head>'
    )
    html_end = "</head>"
    markdown = html_start + markdown + html_end
    return markdown


def render_diff(s1, s2):
    """
    Creates a diff list and returns a string of html with the differences between s1 and s2.
    """
    diff = get_difference(s1, s2)
    return diff_to_html(diff)
