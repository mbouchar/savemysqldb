#!/usr/bin/python
# -*- coding: utf-8

# Create a backup of all mysql databases
# Mathieu Bouchard

from ConfigParser import ConfigParser
from subprocess import Popen, PIPE
import socket, logging, sys, os

CONFIGFILE = "/etc/savemysqldb.conf"
DEFAULT_CONFIG = {"DB_DIR": "/var/lib/mysql",
                  "BACKUP_DIR": "/backup",
                  "MYSQLHOTCOPY_BIN": "/usr/bin/mysqlhotcopy",
                  "DB_USER": "root",
                  "DB_PASSWD": "",
                  "EXCEPTIONS": []}

class Config(object):
    def __init__(self, config_file):
        """Open a configuration file and load it's contents

        @param config_file: The configuration files
        @type config_file: str or [ str ]
        """
        self.__dict__ = DEFAULT_CONFIG
        self.read(config_file)

    def read(self, config_file):
        """Create a dict from the complete file strucure

        @return: The dict read from the config file
        @rtype: { str : { str : str } }
        """
        config = ConfigParser()
        config.read(config_file)

        for section in config.sections():
            for option in config.options(section):
                option = option.upper()
                if option == "EXCEPTIONS":
                    self.__dict__[option] = config.get(section, option).split()
                else:
                    self.__dict__[option] = config.get(section, option)

def findDatabases(config):
    """Find the list of databases that needs to be dumped

    @param config: Program configuration
    @type config: SaveMySQLDBConfig

    @return: The list of databases
    @rtype: [ str ]
    """
    return [x for x in os.listdir(config.DB_DIR) \
            if os.path.isdir(os.path.join(config.DB_DIR, x)) \
               and x not in config.EXCEPTIONS]

def dumpDatabases(databases, config):
    """Create a hot copy of the selected databases using mysqlhotcopy

    @param databases: The list of databases to dump
    @type databases: [ str ]
    @param config: Program configuration
    @type directory: SaveMySQLDBConfig
    """
    if not os.path.exists(config.BACKUP_DIR):
        os.makedirs(config.BACKUP_DIR)
    elif not os.path.isdir(config.BACKUP_DIR):
        raise OSError("%s is not a directory" % config.BACKUP_DIR)

    for database in databases:
        command = [config.MYSQLHOTCOPY_BIN, "--allowold", "-u", config.DB_USER,
                   database, config.BACKUP_DIR]
        if config.DB_PASSWD is not "":
            command.extend(["-p", config.DB_PASSWD])

        process = Popen(command, stdout = PIPE, stderr = PIPE)
        process.wait()
        if process.returncode != 0:
            raise OSError("mysqlhotcopy: %s" % process.communicate()[1])

if __name__ == "__main__":
    # Get program configuration
    config = Config(CONFIGFILE)

    try:
        # Create the list of databases
        databases = findDatabases(config)
        # Dump the databases
        dumpDatabases(databases, config)
    except OSError, e:
        print "%s: %s: %s" % (socket.gethostname(), __file__, str(e))
        sys.exit(1)
