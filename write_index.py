import dominate
import pathlib
import re
import tarfile

from dataclasses import dataclass
from datetime import datetime
from dominate.tags import *


@dataclass(frozen=True)
class LogEntry:
    display_name: str
    date: datetime
    kind: str
    path: pathlib.Path
    href: str


def parse_log_datetime(name: str) -> datetime | None:
    """Parse the log datetime from a directory or archive base name."""
    try:
        return datetime.strptime(name, '%Y-%m-%d_%H-%M-%S')
    except ValueError:
        return None


def get_log_entries() -> list[LogEntry]:
    """Return a sorted list of valid log entries (directories or tar.xz archives).

    Returns:
        A list of LogEntry objects for all valid log directories and archives.
    """

    base_dir = pathlib.Path('log-files')
    entries: list[LogEntry] = []

    for path in base_dir.iterdir():
        if path.is_dir() and (path / 'index.html').is_file():
            date = parse_log_datetime(path.name)
            if date:
                entries.append(LogEntry(
                    display_name=path.name,
                    date=date,
                    kind='dir',
                    path=path,
                    href=f'{path.name}/index.html',
                ))
        elif path.is_file() and path.name.endswith('.tar.xz'):
            base_name = path.name.removesuffix('.tar.xz')
            date = parse_log_datetime(base_name)
            if date:
                entries.append(LogEntry(
                    display_name=base_name,
                    date=date,
                    kind='archive',
                    path=path,
                    href=path.name,
                ))

    return sorted(entries, key=lambda entry: (entry.date, entry.display_name), reverse=True)


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


def read_index_html(entry: LogEntry) -> str:
    """Read index.html content from a directory or a tar.xz archive."""
    if entry.kind == 'dir':
        with open(entry.path / 'index.html', 'r') as index_file:
            return index_file.read()

    if entry.kind == 'archive':
        try:
            with tarfile.open(entry.path, 'r:xz') as tar:
                preferred_suffix = f'{entry.display_name}/index.html'
                member = None
                for candidate in tar.getmembers():
                    if candidate.name == preferred_suffix:
                        member = candidate
                        break
                    if member is None and candidate.name.endswith('/index.html'):
                        member = candidate
                if member is None:
                    return ''
                extracted = tar.extractfile(member)
                if extracted is None:
                    return ''
                with extracted:
                    return extracted.read().decode('utf-8', errors='replace')
        except (tarfile.TarError, OSError):
            return ''

    return ''


def write_index_file(list_of_logs: list[LogEntry]) -> None:
    """Write an index.html file containing hyperlinks to the log file directories contained in this directory.              

    Args:
        list_of_logs: A list of log file entries to put in the index file.

    Returns:
        None.
    """

    doc = dominate.document(title='Index of Valgrind Memcheck output', lang='en')

    dates = [entry.date for entry in list_of_logs]

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
                    for entry in list_of_logs:
                        if entry.date.year == unique_date.year and entry.date.month == unique_date.month:
                            file_content = read_index_html(entry)

                            match = header_regex.search(file_content)
                            green, orange, red = get_summary_numbers(file_content, summary_regex)
                            colour = get_overall_colour(green, orange, red)

                            display_name = entry.display_name
                            if entry.kind == 'archive':
                                display_name = f'{display_name} [archive]'

                            with tr(cls=f'tr-{colour}') as table_row:
                                table_row.add(td(a(display_name, href=entry.href)))
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

    list_of_logs = get_log_entries()
    write_index_file(list_of_logs)
