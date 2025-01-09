from enum import Enum

class Types(Enum):
    RAILROAD = 0,
    CITY = 1,
    CORNER = 2,
    SPECIAL = 3


class Group:
    _id_counter = 0
    id: int
    name: str
    type: str

    @staticmethod
    def reset_id():
        Group._id_counter = 0

    def __init__(self, type: str, name: str):
        self.id = Group._id_counter
        Group._id_counter += 1
        self.name = name
        self.type = type

class Field:
    group: Group
    id: str
    def __init__(self, group: Group, id: str = None):
        self.group = group
        self.id = id
