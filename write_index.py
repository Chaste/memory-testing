import dominate
import pathlib
import re

from datetime import datetime
from dominate.tags import *


def get_list_of_log_file_directories() -> list[str]:
    """Return a sorted list of valid log file directory names.

    Returns:
        A list of strings of all valid log file directories (i.e. those that themselves contain an index.html file).
    """

    base_dir = pathlib.Path('log-files')
    dirs_list = [path.name for path in base_dir.iterdir() if path.is_dir() and (path / 'index.html').is_file()]

    return sorted(dirs_list, reverse=True)


def get_summary_numbers(file_content: str, regex: re.Pattern):
    """
    Extract and return the summary numbers for green, orange, and red statuses from the file content.

    Args:
        file_content: The content of the file as a string.
        regex: A compiled regex that matches the green, orange, and red counts.
    Returns:
        A tuple containing the counts for green, orange, and red statuses respectively.
    """
    match = regex.search(file_content)
    if match and len(match.groups()) == 3:
        return int(match.group(1)), int(match.group(2)), int(match.group(3))

    green_count = file_content.count('No leaks found')
    orange_count = file_content.count('Possible leak found')
    red_count = file_content.count('(RED)')

    return green_count, orange_count, red_count


def get_overall_colour(green: int, orange: int, red: int) -> str:
    """
    Determine the overall color based on the counts of green, orange, and red statuses.

    Args:
        green: Count of green statuses.
        orange: Count of orange statuses.
        red: Count of red statuses.

    Returns:
        A string containing the dominating colour for the table row background, prioritising red, then orange, then
        green, and defaulting to white in the unlikely event of no recognised statuses.
    """
    # if red > 0:
    #     return '#FFADAD'
    # if orange > 0:
    #     return '#FFD6A5'
    # if green > 0:
    #     return '#CAFFBF'
    # return '#FFFFFF'

    if red > 0:
        return 'red'
    if orange > 0:
        return 'orange'
    if green > 0:
        return 'green'
    return 'white'


def write_index_file(list_of_logs: list[str]) -> None:
    """Write an index.html file containing hyperlinks to the log file directories contained in this directory.              

    Args:
        list_of_logs: A list of strings of log file directories to put in the index file.

    Returns:
        None.
    """

    doc = dominate.document(title='Index of Valgrind Memcheck output', lang='en')

    dates = [datetime.strptime(x, '%Y-%m-%d_%H-%M-%S') for x in list_of_logs]

    unique_dates = {datetime(year=date.year, month=date.month, day=1) for date in dates}
    unique_dates = sorted(list(unique_dates), reverse=True)

    # Regex to find the branch name and commit hash for this memtest output
    header_pattern = r'([0-9a-fA-F]{40})">\1<\/a> on branch ([a-zA-Z0-9\-\_\/\.]+)<\/h2>'
    header_regex = re.compile(header_pattern)

    # Regex to find the number of green, orange and red tests in a given file
    summary_pattern = r'green: (\d+).*orange: (\d+).*red: (\d+)'
    summary_regex = re.compile(summary_pattern)

    with doc.head:
        link(rel='stylesheet', href='style.css')
        link(rel='preconnect', href='https://fonts.googleapis.com')
        link(rel='preconnect', href='https://fonts.gstatic.com')
        link(rel='stylesheet', href='https://fonts.googleapis.com/css2?family=Inconsolata&display=swap')

    with doc:

        with div(id='title'):
            h1('Index of Valgrind Memcheck output')

        with div(id='list-by-month'):
            attr(cls='body')
            
            for unique_date in unique_dates:
                h2(unique_date.strftime("%B %Y"))

                with table().add(tbody()):
                    for path, date in zip(list_of_logs, dates):
                        if date.year == unique_date.year and date.month == unique_date.month:

                            with open(f'log-files/{path}/index.html', 'r') as index_file:
                                file_content = index_file.read()

                            match = header_regex.search(file_content)
                            green, orange, red = get_summary_numbers(file_content, summary_regex)
                            colour = get_overall_colour(green, orange, red)

                            with tr(cls=f'tr-{colour}') as table_row:
                                table_row.add(td(a(path, href=f'{path}/index.html')))
                                table_row.add(td(f'{colour}'))
                                if match:
                                    table_row.add(td(match.group(2)))
                                    table_row.add(td(a(match.group(1), href=f'https://github.com/Chaste/Chaste/commit/{match.group(1)}')))
                                else:
                                    table_row.add(td("unknown branch"))
                                    table_row.add(td("unknown commit"))

    with open('log-files/index.html', 'w') as html_file:
        html_file.write(doc.render())


if __name__ == "__main__":

    list_of_logs = get_list_of_log_file_directories()
    write_index_file(list_of_logs)
