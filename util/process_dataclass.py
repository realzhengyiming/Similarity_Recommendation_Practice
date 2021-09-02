from dataclasses import dataclass
from typing import Dict, List

import numpy
import numpy as np
from shapely.geometry import LineString, Polygon


@dataclass
class RoomDataClass:
    id: int = None
    wkt: Polygon = None
    type: int = None
    type_name: str = None

    def is_empty(self):
        if self.id and self.wkt and type:
            return False
        return True

    def __repr__(self):
        return f"{self.type_name} {self.type}"


@dataclass
class PlanDataClass:
    name: str = None
    id: int = None
    wkt: Polygon = None
    main_entrance_wkt: LineString = None
    rooms: List[RoomDataClass] = None


@dataclass
class BedroomDim:
    width: int = None
    long: int = None
    centroid_position: numpy.array = None  # 重心相对位置


@dataclass
class IntermendiateProcess:
    id: int = None
    wkt: Polygon = None
    name: str = None
    main_entrance_wkt: int = None
    rooms: numpy.array = None  # 重心相对位置


@dataclass
class FloorPlanGraph:  # dataclass 如果不给变量类型会失败，写入数据库和读取数据库的东西都用这个来装
    '''
    此处除了客厅是相对于整体的户型的相对位置，其余的房间都是相对于客厅的相对位置,
    把这个写入到数据库中去
    '''
    id: int = None
    plan_graph_area: int = 0
    plan_graph_name: str = None
    plan_graph_lw: List = None
    bedroom_dim_list: List = None  # 有多个
    livingroom_lw: List = None  # todo 用或来进行表示，还是怎么样
    livingroom_xy: List = None
    entrance_xy: List = None  # 门的相对位置

    def parse_from_dict(self, data: Dict):  # 这个data 是直接的file_content传进来的？
        self.id = data.get("id")
        self.plan_graph_area = data.get("plan_graph_area")
        self.plan_graph_name = data.get("plan_graph_name")
        self.plan_graph_lw = np.array(data.get("plan_graph_lw"))  # todo 后面要让数据库每个都不为空，这样读取出来的的数据就一定不是空的了
        self.bedroom_dim_list = [[np.array([i['long'], i['width']]), np.array(i["centroid_position"])]
                                 for i in
                                 data.get("bedroom_dim_list")]

        self.livingroom_lw = np.array(data.get("livingroom_lw"))
        self.livingroom_xy = np.array(data.get("livingroom_xy"))
        self.entrance_xy = np.array(data.get("entrance_xy"))


# 这个是error
class FeatureDictKeyError(Exception):
    def __init__(self, error_info):
        super().__init__(self)  # 初始化父类
        self.error_info = error_info

    def __str__(self):
        return self.error_info
