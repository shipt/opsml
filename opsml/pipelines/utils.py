"""Module pipeline utils"""

from time import gmtime, strftime

import click


def echo(*args, **kwargs):
    """Echo func"""

    click.secho(*args, **kwargs)


def stdout_msg(msg, **kwargs):
    """Prints message to stdout"""

    echo(f"[{get_time()}]", fg="cyan", nl=False)
    echo(f" - {msg}", **kwargs)


def get_time():
    """Gets current time"""

    return strftime("%Y-%m-%d %H:%M:%S", gmtime())
