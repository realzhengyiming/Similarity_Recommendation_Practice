import statistics
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
class PlanGraphWkt:
    id: int = None
    wkt: Polygon = None
    name: str = None
    main_entrance_wkt: Polygon = None
    livingroom_wkt: Polygon = None  # 这个是新增加的，json不带这个
    bedrooms: numpy.array = None  # 重心相对位置,这儿往后直接存平均值，我觉得肯定更不准确的
    other_rooms: List = None  # 这儿是放所有房子的，用来做可视化临时用的
    total_rooms: List = None


@dataclass
class PlanGraphDim:  # dataclass 如果不给变量类型会失败，写入数据库和读取数据库的东西都用这个来装
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

    def parse_from_dict(self, data: Dict):  # 这个data 是直接的 处理后的维度表查询出来的
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


@dataclass
class RemoteComputePlanGraphDim:  # dataclass 如果不给变量类型会失败，写入数据库和读取数据库的东西都用这个来装
    '''
    和上面的PlanGraphDim的区别是，此处把房间使用平均值来代替，然后
    '''
    id: int = None
    plan_area: float = 0
    plan_name: str = None
    plan_l: float = None
    plan_w: float = None
    bedroom_l: float = None  # 有多个  # 存的是多个房间的平均值
    bedroom_w: float = None  # 有多个
    bedroom_x: float = None  # 有多个
    bedroom_y: float = None  # 有多个
    livingroom_l: float = None  # todo 用或来进行表示，还是怎么样
    livingroom_w: float = None  # todo 用或来进行表示，还是怎么样
    livingroom_x: float = None
    livingroom_y: float = None
    entrance_x: float = None  # 门的相对位置
    entrance_y: float = None  # 门的相对位置

    def parse_from_plan_graph_dim(self, plan_graph_dim: PlanGraphDim):  # 这个data 是直接的 处理后的维度表查询出来的
        self.id = plan_graph_dim.id
        self.plan_area = plan_graph_dim.plan_graph_area
        self.plan_name = plan_graph_dim.plan_graph_name
        self.plan_l = plan_graph_dim.plan_graph_lw[0]
        self.plan_w = plan_graph_dim.plan_graph_lw[1]

        self.bedroom_l = statistics.mean([i['long'] for i in plan_graph_dim.bedroom_dim_list])
        self.bedroom_w = statistics.mean([i['width'] for i in plan_graph_dim.bedroom_dim_list])
        self.bedroom_x = statistics.mean([i['centroid_position'][0] for i in plan_graph_dim.bedroom_dim_list])
        self.bedroom_y = statistics.mean([i['centroid_position'][1] for i in plan_graph_dim.bedroom_dim_list])

        self.livingroom_l = plan_graph_dim.livingroom_lw[0]
        self.livingroom_w = plan_graph_dim.livingroom_lw[1]
        self.livingroom_x = plan_graph_dim.livingroom_xy[0]
        self.livingroom_y = plan_graph_dim.livingroom_xy[1]

        self.entrance_x = plan_graph_dim.entrance_xy[0]
        self.entrance_y = plan_graph_dim.entrance_xy[1]


@dataclass
class FeatureWeight:
    livingroom_xy_weight: float = 5.0
    livingroom_lw_weight: float = 5.0
    bedroom_xy_weight: float = 5.0
    bedroom_lw_weight: float = 5.0
    plan_lw_weight: float = 5.0
    entrance_xy_weight: float = 5.0


# 这个是error的类
class FeatureDictKeyError(Exception):
    def __init__(self, error_info):
        super().__init__(self)  # 初始化父类
        self.error_info = "lack of feature error" if not error_info else error_info

    def __str__(self):
        return self.error_info


# 缺少element 错误
class LackOfRoomTypeError(Exception):
    def __init__(self, error_info):
        super().__init__(self)  # 初始化父类
        self.error_info = "lack of room type error" if not error_info else error_info

    def __str__(self):
        return self.error_info
