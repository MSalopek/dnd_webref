from abc import ABC
from abc import ABCMeta
from abc import abstractmethod


class CommandMeta(ABCMeta):
    """Metaclass that handles command classes registration"""
    All = {}
    Command = {}

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        try:
            for x in attrs['names']:
                CommandMeta.Command[x] = cls()
            CommandMeta.All[name] = cls()
        except:
            pass


class AbstractCommand(ABC, metaclass=CommandMeta):

    @property
    @abstractmethod
    def names(self):
        """list of command aliases for
        commandline use; ex: [command, cm, comm]"""
        pass

    @property
    @abstractmethod
    def desc(self):
        """command action description (short or long)"""
        pass

    @abstractmethod
    def Run(self):
        pass
