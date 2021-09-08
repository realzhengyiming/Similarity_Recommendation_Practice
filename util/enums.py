from enum import Enum


class OutputRoomType(Enum):
    ROOM_TYPE_UNKNOWN = 0
    BEDROOM = 1
    MASTER_BEDROOM = 2
    SECONDARY_BEDROOM = 3
    LIVING_ROOM = 4
    DINING_ROOM = 5
    DINING_LIVING_ROOM = 6
    KITCHEN = 7
    BATHROOM = 8
    MASTER_BATHROOM = 9
    GUEST_BATHROOM = 10
    CLOAK_ROOM = 11
    CHILDREN_ROOM = 12
    BALCONY = 13
    PASSAGE = 14
    HALLWAY = 15
    CORRIDOR = 16
    ELEVATOR = 17
    ANTECHAMBER = 18
    STAIRWELL = 19
    MECHANICAL_ROOM = 20
    OPEN_KITCHEN = 21
    PUBLIC_AREA = 22
    STUDIO = 23
    CHINESE_KITCHEN = 24
    ENTRANCE_GARDEN = 25
    STORAGE_ROOM = 26
    LAUNDRY = 27
    EQUIPMENT_PLATFORM = 28
    AC = 29
    NANNY_ROOM = 30
    SENIOR_ROOM = 31
    PARTY_ROOM = 32
    SERVICE_BALCONY = 33

    @classmethod
    def get_var_name_by_value(cls, value):
        enums_data = dict(OutputRoomType.__members__.items())
        for key in enums_data:
            temp_value = enums_data[key].value
            if temp_value == value:
                return key
        return None


LIVING_ROOM_ENUM_TYPES = {
    OutputRoomType.LIVING_ROOM.value,
    OutputRoomType.DINING_ROOM.value,
    OutputRoomType.DINING_LIVING_ROOM.value,

    # OutputRoomType.PASSAGE.value,  # 这个是思和之前处理的思路
    # OutputRoomType.HALLWAY.value,
    # OutputRoomType.PUBLIC_AREA.value,
    # OutputRoomType.ENTRANCE_GARDEN.value
}

BEDROOM_ENUMS_TYPE = {
    OutputRoomType.BEDROOM.value,
    OutputRoomType.MASTER_BEDROOM.value,
    OutputRoomType.SECONDARY_BEDROOM.value,

    # 根据单体那边的核对
    OutputRoomType.SENIOR_ROOM,
    OutputRoomType.CHILDREN_ROOM,
    OutputRoomType.NANNY_ROOM,
    OutputRoomType.STUDIO,
    OutputRoomType.PARTY_ROOM
}

if __name__ == '__main__':
    result = OutputRoomType.get_var_name_by_value(1)

    print(result)
