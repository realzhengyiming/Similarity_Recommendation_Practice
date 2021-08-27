import json
import os
from dataclasses import dataclass

import cv2
import numpy as np
from shapely.ops import unary_union
from shapely.wkt import loads

@dataclass
class FloorPlanGraphDataClass:


class FloorPlanGraph:
    def __init__(self):
        self.id = None
        self.plan_graph_wl_dim = None
        self.bedroom_dim_list = []
        self.livingroom_wl = None
        self.area = 0
        self.name = ''
        self.entrance_xy_dim = None
        self.livingroom_position = None

    def set_livingroom_position_dim(self, feat):  # 这个是客厅重心相较于户型图重心的相对位置（重心相减）
        self.livingroom_position = feat

    def set_livingroom_wl_dim(self, feat):  # 这儿可以看到living room 只有一个
        self.livingroom_wl = feat

    def set_bedroom_dim(self, feat):
        self.bedroom_dim_list.append(feat)

    def set_plan_id(self, id):
        self.id = id

    def centorid2npy(self, centroid):  # 提取出了重心的x 和y的坐标，这个时候做偏移吗
        return np.array([centroid.x, centroid.y], np.int16)

    def from_json(self, json_path):  # 所有的数据预处理都在这儿了，并没有很复杂
        _, filename = os.path.split(json_path)

        plan_graph_dict = json.load(open(json_path, 'r'))  # 从json文件中读取

        self.name = json_path
        self.area = loads(plan_graph_dict['wkt']).area / 1e6
        self.set_plan_id(plan_graph_dict['id'])
        # id 也存起来，到时候直接把对应的id返回给前段再让他们自己查询就好了，

        ###
        plan_envelope_bounds = loads(plan_graph_dict['wkt']).envelope.bounds  # 那这个还是外接矩形的重心
        plan_width = plan_envelope_bounds[2] - plan_envelope_bounds[0]
        plan_long = plan_envelope_bounds[3] - plan_envelope_bounds[1]
        self.plan_graph_wl_dim = np.array([plan_width, plan_long], np.int16)

        ###
        living_room_list = []
        for room in plan_graph_dict['rooms']:
            if room['type'] in {4, 5, 6, 14, 15, 22, 25}:
                living_room_list.append(loads(room['wkt']))
        living_room = unary_union(living_room_list)  # 多个小的living 合并成了同一个living room
        ## 这儿开始插入相对应的计算偏移，如果都是以重心作为各个组件的代表意义的话，可以考虑增加夹角作为参数求，先把坐标处理好。

        ##
        # p = living_room.envelope  # 信封是啥，就是外接最小包裹矩形的 geometry啊
        living_room_bounds = living_room.envelope.bounds  # 这个是外接矩形把，刚好四个点，得到了对应的额 长 和 宽
        livingroom_width = living_room_bounds[2] - living_room_bounds[0]
        livingroom_long = living_room_bounds[3] - living_room_bounds[1]  # 宽和高的意思，原来是这样的
        self.set_livingroom_wl_dim(np.array([livingroom_width, livingroom_long], np.int16))

        ### 初始化 客厅相较于户型图的相对位置的信息
        plan_graph_centroid_npy = self.centorid2npy(loads(plan_graph_dict['wkt']).envelope.centroid)
        living_room_centroid_npy = self.centorid2npy(living_room.envelope.centroid)
        self.set_livingroom_position_dim(living_room_centroid_npy - plan_graph_centroid_npy)

        ###
        entrance_centroid = loads(plan_graph_dict['main_entrance_wkt']).centroid  # 这儿每个部件都 取了他们的 重心的值作为替代这个多边形的东西
        self.entrance_xy_dim = self.centorid2npy(
            entrance_centroid) - living_room_centroid_npy  # 门的这儿是存的是，门和 living room的重心。

        ###
        if living_room_centroid_npy is not None:
            for room in plan_graph_dict['rooms']:
                if type(room) == type(None):
                    continue
                if room['type'] in {1, 2, 3}:
                    room_bounds = loads(room['wkt']).bounds
                    room_width = room_bounds[2] - room_bounds[0]
                    room_long = room_bounds[3] - room_bounds[1]
                    room_centroid_npy = self.centorid2npy(
                        loads(room['wkt']).envelope.centroid) - living_room_centroid_npy  # 这儿的卧室，也是和
                    self.set_bedroom_dim(
                        np.array([room_centroid_npy[0], room_centroid_npy[1],
                                  room_width, room_long], np.int16))

    def vis_graph(self):
        cs = 256
        img = np.zeros([cs, cs, 3])
        _, _, w, h = self.set_livingroom_wl_dim
        w = np.int32(w // 200)
        h = np.int32(h // 200)
        cv2.rectangle(img, (cs // 2 - w, cs // 2 - h), (cs // 2 + w, cs // 2 + h), (0, 0, 255), -1)
        for idx, i in enumerate(self.bedroom_dim_list):
            dx, dy, w, h = i
            w = np.int32(w // 200)  # 这是缩小呢，这儿就进行了对应的数据处理
            h = np.int32(h // 200)
            x = np.int32(dx // 100)
            y = np.int32(dy // 100)
            cv2.rectangle(img, (cs // 2 + x - w, cs // 2 + y - h), (cs // 2 + x + w, cs // 2 + y + h),
                          (255 - 80 * idx, 0, 0), -1)
        return img


if __name__ == '__main__':
    pass
