import json
from dataclasses import asdict
from typing import Dict, List

import numpy as np
import pandas as pd
from shapely import wkt
from shapely.geometry import LineString, Polygon
from shapely.ops import linemerge, unary_union

from constant import insert_floor_graph_dim_sql, select_file_content_sql
from util.db import data_session_instance
from util.enums import living_room_enum_type, bedroom_enums_type
from util.process_dataclass import FeatureDictKeyError, FloorPlanGraph, BedroomDim, IntermendiateProcess


class FeatureProcess:
    def __init__(self, query_result_row: Dict):
        '''
        :param query_result_row:  输入的是直接使从file—content 按字典读取出来的一行结果
        '''
        self.query_result_row = query_result_row
        self.one_project = self.query_result_row['content']
        need_keys = {'doors', "nodes", "rooms", "walls"}
        key_union = set(self.one_project.get("layout_unit").keys()) & need_keys
        if key_union != need_keys:
            raise FeatureDictKeyError("dict don't have the necessary keys")

    def parse_intermediate_polygon(self):
        self._extract_rooms_geom()
        self._extract_main_enterance_geom()
        self._set_import_room()

        # 获得对应的中间表的 polygon 用于可视化
        intermendiate_polygon = IntermendiateProcess()
        intermendiate_polygon.id = self.one_project.get("id")
        intermendiate_polygon.name = self.one_project.get("layout_unit").get("name")

        intermendiate_polygon.main_entrance_wkt = self.main_entrance_wkt
        intermendiate_polygon.wkt = self.plan_wkt
        intermendiate_polygon.rooms = self.total_room_geom_list
        return intermendiate_polygon

    def _relative_xy_to_npy(self, centroid, reference_centroid):
        result = np.array([centroid.x, centroid.y], np.int16) - np.array([reference_centroid.x, reference_centroid.y],
                                                                         np.int16)
        result = [int(i) for i in list(result)]
        return result

    def _extract_rooms_geom(self):
        plan = self.one_project.get("layout_unit")
        self.living_room_geom_list = []
        self.bedroom_geom_list = []
        self.other_geom_list = []
        for room in plan['rooms']:
            wall_geom_list = []
            for wall_id in room['wall_id_list']:
                nested_node_list = {node['id']: node for node in plan['nodes']}
                nested_wall_list = {wall['id']: wall for wall in plan['walls']}

                src_x = nested_node_list[nested_wall_list[wall_id]['source_id']]['x']
                src_y = nested_node_list[nested_wall_list[wall_id]['source_id']]['y']
                dst_x = nested_node_list[nested_wall_list[wall_id]['target_id']]['x']
                dst_y = nested_node_list[nested_wall_list[wall_id]['target_id']]['y']

                wall_geom_list.append(LineString([[src_x, src_y], [dst_x, dst_y]]))

            room_polygon = Polygon(list(linemerge(wall_geom_list).coords))
            if room['room_type'] in living_room_enum_type:  # 客厅类型
                self.living_room_geom_list.append(room_polygon)
            elif room['room_type'] in bedroom_enums_type:  # 卧室类型
                self.bedroom_geom_list.append(room_polygon)
            else:
                self.other_geom_list.append(room_polygon)  # 需要保留用来拼整个户型图

    def _safe_union_polygon_list(self, geom_list):
        assert len(geom_list) != 0  # 如果图片不等于就会爆出错误，说明矩阵也是5行6列的了
        if len(geom_list) > 1:
            total_geom_wkt = unary_union(geom_list)
        else:
            total_geom_wkt = geom_list[0]
        return total_geom_wkt

    def _set_import_room(self):
        total_room_geom_list = self.living_room_geom_list + self.bedroom_geom_list + self.other_geom_list
        self.plan_wkt = self._safe_union_polygon_list(total_room_geom_list)
        self.living_room_wkt = self._safe_union_polygon_list(self.living_room_geom_list)
        self.total_room_geom_list = total_room_geom_list

    def _extract_main_enterance_geom(self):
        doors = self.one_project['layout_unit']['doors']
        for door in doors:
            if door['main_entrance']:
                door_node = [[i['x'], i['y']] for i in door['coordinates']]
                door_wkt = LineString(door_node)
                self.main_entrance_wkt = door_wkt

    def parse_to_plan_floor_graph_by_json(self, data:Dict):
        plan_floor_graph = FloorPlanGraph()
        plan_floor_graph.id = data.get("id")
        self.plan_wkt = wkt.loads(data.get("wkt"))
        plan_floor_graph.plan_graph_area = self.plan_wkt.area
        plan_floor_graph.plan_graph_lw = self._get_plan_lw()
        plan_floor_graph.bedroom_dim_list =
        plan_floor_graph.livingroom_lw =
        plan_floor_graph.livingroom_xy =
        plan_floor_graph.entrance_xy =


        return plan_floor_graph

        plan_graph_lw: List = None
        bedroom_dim_list: List = None  # 有多个
        livingroom_lw: List = None  # todo 用或来进行表示，还是怎么样
        livingroom_xy: List = None
        entrance_xy: List = None  # 门的相对位置

    def _get_plan_lw(self)->List:
        plan_envelope_bounds = self.plan_wkt.envelope.bounds  # 那这个还是外接矩形的重心
        plan_width = plan_envelope_bounds[2] - plan_envelope_bounds[0]
        plan_long = plan_envelope_bounds[3] - plan_envelope_bounds[1]
        return [plan_long, plan_width]

    def parse_to_plan_floor_graph(self):
        self._extract_rooms_geom()
        self._extract_main_enterance_geom()
        self._set_import_room()
        plan_floor_graph = FloorPlanGraph()

        # 获得户型的长宽
        plan_floor_graph.plan_graph_lw = self._get_plan_lw()
        plan_floor_graph.plan_graph_name = self.one_project.get("layout_unit").get("name")
        plan_floor_graph.id = self.query_result_row.get("id")
        plan_floor_graph.plan_graph_area = self.plan_wkt.area / 1e6  # 单位是毫米

        # 处理livingroom的相对位置和长宽
        living_room_bounds = self.living_room_wkt.envelope.bounds  # 这个是外接矩形把，刚好四个点，得到了对应的额 长 和 宽
        livingroom_width = living_room_bounds[2] - living_room_bounds[0]
        livingroom_long = living_room_bounds[3] - living_room_bounds[1]  # 宽和高的意思，原来是这样的
        plan_floor_graph.livingroom_lw = [livingroom_long, livingroom_width]
        plan_floor_graph.livingroom_xy = self._relative_xy_to_npy(self.living_room_wkt.centroid,
                                                                  self.plan_wkt.envelope.centroid)

        # 处理主入口的相对位置
        plan_floor_graph.entrance_xy = self._relative_xy_to_npy(self.main_entrance_wkt.centroid,
                                                                self.plan_wkt.envelope.centroid)

        # 处理户型里面的房间(bedroom)
        for room in self.bedroom_geom_list:
            room_bounds = room.bounds
            room_width = room_bounds[2] - room_bounds[0]
            room_long = room_bounds[3] - room_bounds[1]

            bedroom_dim = BedroomDim()
            bedroom_dim.long, bedroom_dim.width = room_long, room_width
            bedroom_dim.centroid_position = self._relative_xy_to_npy(room.centroid, self.plan_wkt.envelope.centroid)
            bedroom_dim_dict = asdict(bedroom_dim)
            if not plan_floor_graph.bedroom_dim_list:
                plan_floor_graph.bedroom_dim_list = [bedroom_dim_dict]
            else:
                plan_floor_graph.bedroom_dim_list.append(bedroom_dim_dict)

        return plan_floor_graph


def insert_into_train_data_table(row_data):  # TODO (zym 20210902)这部分应该写到airflow 中去定时调用
    feature_process = FeatureProcess(row_data)
    result = feature_process.parse_to_plan_floor_graph()  # 是的，我要把这个填充好，填充好后就可以把这个写入到数据库中了。
    data = asdict(result)
    sql = insert_floor_graph_dim_sql.format(
        id=data['id'],
        plan_graph_lw=json.dumps(data['plan_graph_lw']),
        plan_graph_area=data['plan_graph_area'],
        plan_graph_name=data['plan_graph_name'],
        bedroom_dim_list=json.dumps(data['bedroom_dim_list']),
        livingroom_xy=json.dumps(data['livingroom_xy']),
        livingroom_lw=json.dumps(data['livingroom_lw']),
        entrance_xy=json.dumps(data['entrance_xy'])
    )
    with data_session_instance.get_engine().connect() as conn:
        print(sql)
        conn.execute(sql)


def main():  # todo 把表的数据写入到redis中
    with data_session_instance.get_engine().connect().execution_options(stream_results=True) as conn:
        for chunk_dataframe in pd.read_sql(select_file_content_sql, conn, chunksize=100):
            for index, row in chunk_dataframe.iterrows():  # 每次对这个进行处理
                data = dict(row)
                insert_into_train_data_table(data)  # 正常的
    print("done!")


if __name__ == '__main__':
    # main()  # 这个是处理中间值的
    # 这儿有22827条数据

    select_file_content_sql = '''
    SELECT * FROM file_content where file_type='RESIDENTIAL_UNIT' limit 10;
    '''

    with data_session_instance.get_engine().connect().execution_options(stream_results=True) as conn:  # 这个主要是根据结果用来做可视化的
        for chunk_dataframe in pd.read_sql(select_file_content_sql, conn, chunksize=100):
            for index, row in chunk_dataframe.sample(1).iterrows():  # 每次对这个进行处理
                data = dict(row)
                feature = FeatureProcess(data)
                result = feature.parse_intermediate_polygon()
                print(result)

