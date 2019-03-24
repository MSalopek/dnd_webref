import os
import sys
import logging
import sqlite3
import pathlib

from default_config import getDefaultPaths
from command import CommandMeta
from scripts import *

logger = logging.getLogger(__name__)


def help_message():
    required = "Required args:\n\t[--db] database absolute path\n\n"
    commands = 'Commands (choose one):\n' + "\n".join([
        f"{x.names}:\t{x.desc}" for x in CommandMeta.All.values()
    ]) + "\n['run_all']:\t\t\tParse all files and fill all tables\n"
    options = "\nOptions:\n['-v', '--verbose']:\t\tSet verbose logger output\n"
    example = "\nUsage: python3 command --db '/path_to/database/storage.sqlite'"
    return required + commands + options + example


def mapDefaultPathsToCommands():
    current_path = pathlib.Path.cwd()
    default_paths = getDefaultPaths()
    mapping = {}
    for k,v in CommandMeta.All.items():
        for alias in v.names:
            path = pathlib.Path(default_paths[k])
            mapping[alias] = str(pathlib.Path.joinpath(current_path, path))
    return mapping


def checkPaths(paths_list):
    checked_paths = {path: os.path.exists(path) for path in paths_list}    
    invalid = []
    for k,v in checked_paths.items():
        if not v:
            invalid.append(k)
    if invalid:
        raise FileNotFoundError(f"invalid path.\nPath does not exist {invalid}")


def connectDB(args_list):    
    try:
        if "--db" not in args_list:
            raise ValueError("Missing required argument --db") 
        db_path = args_list.pop(args_list.index("--db")+1)
        checkPaths([db_path])
        db_conn = sqlite3.connect(db_path)
        return db_conn
    except Exception as e:
        logger.error(e)
        print(help_message())
        sys.exit()
   

def setVerbose(args_list):
    if '-v' in sys.argv or '--verbose' in args_list:
        logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(asctime)s [%(name)s]: %(message)s',
                    datefmt='%m-%d %H:%M')
    else:
        logging.basicConfig(level=logging.ERROR,
                    format='[%(levelname)s] %(asctime)s [%(name)s]: %(message)s',
                    datefmt='%m-%d %H:%M')


if len(sys.argv) > 1:
    command_str = sys.argv.pop(1)
    default_paths_map = mapDefaultPathsToCommands()
    setVerbose(sys.argv)

    if command_str == "-h" or command_str == "--help":
        print(help_message())
    elif command_str in CommandMeta.Command.keys():
        db_conn = connectDB(sys.argv)
        command = CommandMeta.Command[command_str]
        command.Run(db_conn, default_paths_map[command_str])
    elif command_str == "run_all":
        db_conn = connectDB(sys.argv)
        for command in CommandMeta.All.values():
            command.Run(db_conn, default_paths_map[command.names[0]])
    else:
        print("Command not found", "\n", "-"*50)
        print(help_message())
else:
    print("# No commands invoked.\n# See available commands listed below.")
    print(help_message())
