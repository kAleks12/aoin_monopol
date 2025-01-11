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
    property_cost: int

    @staticmethod
    def reset_id():
        Group._id_counter = 0

    def __init__(self, type: str, name: str, property_cost: int = None):
        self.id = Group._id_counter
        Group._id_counter += 1
        self.name = name
        self.type = type
        self.property_cost = property_cost

class Field:
    group: Group
    id: str
    buy_cost: int
    def __init__(self, group: Group, id: str = None, buy_cost: int = None):
        self.group = group
        self.id = id
        self.buy_cost = buy_cost
