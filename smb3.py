#! /usr/bin/env python3
# -*- coding: utf-8; py-indent-offset: 4 -*-
#
# Author:  Linuxfabrik GmbH, Zurich, Switzerland
# Contact: info (at) linuxfabrik (dot) ch
#          https://www.linuxfabrik.ch/
# License: The Unlicense, see LICENSE file.

# https://github.com/Linuxfabrik/monitoring-plugins/blob/main/CONTRIBUTING.rst

"""Provides functions to establish SMB connections.
"""

__author__ = 'Linuxfabrik GmbH, Zurich/Switzerland'
__version__ = '2022062001'

import sys

from .globals3 import STATE_UNKNOWN
try:
    import smbclient
except ImportError as e:
    print('Python module "smbclient" is not installed.')
    sys.exit(STATE_UNKNOWN)
try:
    import smbprotocol.exceptions
except ImportError as e:
    print('Python module "smbprotocol" is not installed.')
    sys.exit(STATE_UNKNOWN)


def open_file(path, username, password, timeout, encrypt=True):
    try:
        return (True, smbclient.open_file(
            path,
            mode='rb',
            username=username,
            password=password,
            connection_timeout=timeout,
            encrypt=encrypt,
        ))
    except (smbprotocol.exceptions.SMBAuthenticationError, smbprotocol.exceptions.LogonFailure):
        return (False, 'Login failed')
    except smbprotocol.exceptions.SMBOSError as e:
        if isinstance(e.__context__, smbprotocol.exceptions.FileIsADirectory):
            return (False, 'The file that was specified as a target is a directory, should be a file.')
        if isinstance(e.__context__, smbprotocol.exceptions.ObjectNameNotFound):
            return (False, 'No such file or directory on the smb server.')
        return (False, 'I/O error "{}" while opening or reading {}'.format(e.strerror, path))
    except Exception as e:
        return (False, 'Unknown error opening or reading {}:\n{}'.format(path, e))


def glob(path, username, password, timeout, pattern='*', encrypt=True):
    try:
        file_entry = smbclient._os.SMBDirEntry.from_path(
            path,
            username=username,
            password=password,
            connection_timeout=timeout,
            encrypt=encrypt,
        )

        if file_entry.is_file():
            return (True, [file_entry])

        # converting generator to list here to trigger any exception when accessing files now. this could probably be improved
        return (True, list(smbclient.scandir(
            path,
            mode='rb',
            username=username,
            password=password,
            connection_timeout=timeout,
            search_pattern=pattern,
            encrypt=encrypt,
        )))
    except (smbprotocol.exceptions.SMBAuthenticationError, smbprotocol.exceptions.LogonFailure):
        return (False, 'Login failed')
    except smbprotocol.exceptions.SMBOSError as e:
        if isinstance(e.__context__, smbprotocol.exceptions.ObjectNameNotFound):
            return (False, 'No such file or directory on the smb server.')
        if e.strerror == 'No such file or directory':
            return (True, [])
        return (False, 'I/O error "{}" while opening or reading {}'.format(e.strerror, path))
    except Exception as e:
        return (False, 'Unknown error opening or reading {}:\n{}'.format(path, e))
