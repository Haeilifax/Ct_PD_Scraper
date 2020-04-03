"""Adapter module for MySQLdb to provide more pythonic interface"""

import MySQLdb as mysqldb

# We import * to use this module as a drop in replacement for MySQLdb.connections
from MySQLdb.connections import *


class ConnectionAdapter(mysqldb.connections.Connection):
    """Adapter class to provide context manager for MySQLdb connection"""

    def __enter__(self):
        pass

    def __exit__(self, *args):
        if args[0] is None:
            self.commit()
        else:
            self.rollback()


def connect(*args, **kwargs):
    """Replacement connect method to use ConnectionAdapter"""
    return ConnectionAdapter(*args, **kwargs)
