import json
import time
from dataclasses import asdict
from typing import Dict

import pandas as pd
from shapely import wkt
from shapely.geometry import LineString, Polygon
from shapely.ops import linemerge

from constant import insert_floor_graph_dim_sql, select_file_content_sql, insert_new_plan_graph_dim_sql, \
    create_necessary_table_sql
from util.dataclasses import FeatureDictKeyError, PlanGraphDim, BedroomDim, PlanGraphWkt, \
    RemoteComputePlanGraphDim
from util.db import data_session_instance
from util.enums import LIVING_ROOM_ENUM_TYPES, BEDROOM_ENUMS_TYPE
from util.utils import safe_union_polygon_list, relative_xy_to_npy


class FeatureProcess:
    def __init__(self):
        '''
        :param query_result_row:  输入的是直接使从file—content 按字典读取出来的一行结果
        两个输入，一个直接传过来中间过程  json
        另一个是直接从file_content 传过来
        最终都要输出成一个处理好后的对象，用来存入数据库，或者依靠这个来 给下一步计算用
        '''

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
            if room['room_type'] in LIVING_ROOM_ENUM_TYPES:  # 客厅类型
                self.living_room_geom_list.append(room_polygon)
            elif room['room_type'] in BEDROOM_ENUMS_TYPE:  # 卧室类型
                self.bedroom_geom_list.append(room_polygon)
            else:
                self.other_geom_list.append(room_polygon)  # 需要保留用来拼整个户型图

    def _set_import_room(self):
        total_room_geom_list = self.living_room_geom_list + self.bedroom_geom_list + self.other_geom_list
        self.plan_wkt = safe_union_polygon_list(total_room_geom_list)
        self.living_room_wkt = safe_union_polygon_list(self.living_room_geom_list)
        self.total_room_geom_list = total_room_geom_list

    def _extract_main_enterance_geom(self):
        doors = self.one_project['layout_unit']['doors']
        for door in doors:
            if door['main_entrance']:
                door_node = [[i['x'], i['y']] for i in door['coordinates']]
                door_wkt = LineString(door_node)
                self.main_entrance_wkt = door_wkt

    def _parse_plan_graph_wkt_by_json(self, json_data: Dict):
        intermendiate_process = PlanGraphWkt()

        intermendiate_process.id = json_data.get("id")  # 传过来的是用来做匹配的，所以对它的id不感冒
        intermendiate_process.wkt = wkt.loads(json_data.get("wkt"))
        intermendiate_process.name = "target_plan_graph"
        intermendiate_process.main_entrance_wkt = wkt.loads(json_data.get("main_entrance_wkt"))
        intermendiate_process.bedrooms = [wkt.loads(i['wkt']) for i in json_data.get("rooms") if
                                          i['type'] in BEDROOM_ENUMS_TYPE]  # 这边也是存储需要计算的类型，那就只有bedroom polygon
        livingroom_list = [wkt.loads(i['wkt']) for i in json_data.get("rooms") if
                           i['type'] in LIVING_ROOM_ENUM_TYPES]
        intermendiate_process.livingroom_wkt = safe_union_polygon_list(livingroom_list)

        self.intermendiate_process = intermendiate_process  # 之后再统一由这个中间对象转成graph

    def _extranct_all_import_elements(self, query_result_row):
        self.query_result_row = query_result_row
        self.plan_id = query_result_row.get("file_id")
        self.one_project = self.query_result_row['content']
        need_keys = {'doors', "nodes", "rooms", "walls"}
        key_union = set(self.one_project.get("layout_unit").keys()) & need_keys
        if key_union != need_keys:
            raise FeatureDictKeyError(f"dict don't have the necessary keys. now just have{key_union} need {need_keys}")

        self._extract_rooms_geom()
        self._extract_main_enterance_geom()
        self._set_import_room()

    def _parse_intermediate_polygon(self, query_result_row: Dict):
        self._extranct_all_import_elements(query_result_row)

        # 获得对应的中间表的 polygon 用于可视化
        intermendiate_process = PlanGraphWkt()
        intermendiate_process.id = self.plan_id
        intermendiate_process.name = self.one_project.get("layout_unit").get("name")

        intermendiate_process.main_entrance_wkt = self.main_entrance_wkt
        intermendiate_process.wkt = self.plan_wkt
        intermendiate_process.bedrooms = self.bedroom_geom_list  # 不如只装一个bedroom的list
        intermendiate_process.livingroom_wkt = self.living_room_wkt
        intermendiate_process.other_rooms = self.other_geom_list
        intermendiate_process.total_rooms = self.other_geom_list + self.living_room_geom_list + self.bedroom_geom_list

        self.intermendiate_process = intermendiate_process

    def _fill_plan_graph_obj(self, plan_graph: PlanGraphDim) -> PlanGraphDim:
        # 获得户型的长宽
        plan_envelope_bounds = self.intermendiate_process.wkt.envelope.bounds  # 那这个还是外接矩形的重心
        plan_width = plan_envelope_bounds[2] - plan_envelope_bounds[0]
        plan_long = plan_envelope_bounds[3] - plan_envelope_bounds[1]
        plan_graph.plan_graph_lw = [plan_long, plan_width]

        plan_graph.plan_graph_name = self.intermendiate_process.name
        plan_graph.id = self.intermendiate_process.id
        plan_graph.plan_graph_area = self.intermendiate_process.wkt.area / 1e6  # 单位是毫米

        # 处理livingroom的相对位置和长宽
        living_room_bounds = self.intermendiate_process.livingroom_wkt.envelope.bounds  # 这个是外接矩形把，刚好四个点，得到了对应的额 长 和 宽
        livingroom_width = living_room_bounds[2] - living_room_bounds[0]
        livingroom_long = living_room_bounds[3] - living_room_bounds[1]  # 宽和高的意思，原来是这样的
        plan_graph.livingroom_lw = [livingroom_long, livingroom_width]
        plan_graph.livingroom_xy = relative_xy_to_npy(self.intermendiate_process.livingroom_wkt.centroid,
                                                      self.intermendiate_process.wkt.envelope.centroid)

        # 处理主入口的相对位置
        plan_graph.entrance_xy = relative_xy_to_npy(self.intermendiate_process.main_entrance_wkt.centroid,
                                                    self.intermendiate_process.wkt.envelope.centroid)

        # 处理户型里面的房间(bedroom)
        for room in self.intermendiate_process.bedrooms:  # 存的就是需要的bedroom
            room_bounds = room.bounds
            room_width = room_bounds[2] - room_bounds[0]
            room_long = room_bounds[3] - room_bounds[1]

            bedroom_dim = BedroomDim()
            bedroom_dim.long, bedroom_dim.width = room_long, room_width
            bedroom_dim.centroid_position = relative_xy_to_npy(room.centroid,
                                                               self.intermendiate_process.wkt.envelope.centroid)
            bedroom_dim_dict = asdict(bedroom_dim)
            if not plan_graph.bedroom_dim_list:
                plan_graph.bedroom_dim_list = [bedroom_dim_dict]
            else:
                plan_graph.bedroom_dim_list.append(bedroom_dim_dict)
        return plan_graph

    def parse_to_plan_by_json(self, json_data: Dict) -> PlanGraphDim:
        '''
        这儿传入的是思和那边那种处理好wkt的json
        :param json_data:
        :return:
        '''
        plan_graph = PlanGraphDim()

        self._parse_plan_graph_wkt_by_json(json_data)
        plan_graph = self._fill_plan_graph_obj(plan_graph)
        return plan_graph

    def parse_to_plan_graph(self, query_result_row: Dict) -> PlanGraphDim:
        plan_graph = PlanGraphDim()
        self._parse_intermediate_polygon(query_result_row)
        plan_graph = self._fill_plan_graph_obj(plan_graph)
        return plan_graph

    def parse_to_remote_compute_plan_graph(self, query_result_row: Dict) -> RemoteComputePlanGraphDim:
        '''
        这个是转化为新的plan——graph 对象，服务于，把字段完全拆开放到单一的列中，然后主要的计算放到了postgres 中去做，
        然后这儿对多个房间的匹配，直接简化成使用多个房间（bedroom）的平均值来代替多个房间，其他同上
        :return:
        '''
        plan_graph = self.parse_to_plan_graph(query_result_row)
        remote_plan_graph = RemoteComputePlanGraphDim()
        remote_plan_graph.parse_from_plan_graph_dim(plan_graph)

        return remote_plan_graph

    def parse_to_remote_compute_plan_graph_by_json(self, json_data: Dict) -> RemoteComputePlanGraphDim:
        '''
        这个是转化为新的plan——graph 对象，服务于，把字段完全拆开放到单一的列中，然后主要的计算放到了postgres 中去做，
        然后这儿对多个房间的匹配，直接简化成使用多个房间（bedroom）的平均值来代替多个房间，其他同上
        :return:
        '''
        plan_graph = self.parse_to_plan_by_json(json_data)
        remote_plan_graph = RemoteComputePlanGraphDim()
        remote_plan_graph.parse_from_plan_graph_dim(plan_graph)

        return remote_plan_graph


def insert_into_train_data_table(row_data):  # TODO (zym 20210902)这部分应该写到airflow 中去定时调用
    feature_process = FeatureProcess()
    result = feature_process.parse_to_plan_graph(row_data)  # 是的，我要把这个填充好，填充好后就可以把这个写入到数据库中了。
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
        conn.execute(sql)


def main():
    with data_session_instance.get_engine().connect().execution_options(stream_results=True) as conn:
        for chunk_dataframe in pd.read_sql(select_file_content_sql, conn, chunksize=100):
            for index, row in chunk_dataframe.iterrows():  # 每次对这个进行处理
                data = dict(row)
                insert_into_train_data_table(data)  # 正常的
    print("done!")


# --- new dim table use this operate
def insert_into_new_dim(sql):  # 这个是每次都创建连接的意思吗，好像是，难怪那么慢？,可以添加多行以后再执行插入
    with data_session_instance.get_engine().connect() as write_conn:
        write_conn.execute(sql)


failed_id_list = []


def start_new_process():
    with data_session_instance.get_engine().connect().execution_options(
            stream_results=True) as conn:  # 这个主要是根据结果用来做可视化的

        # 再创建一个连接，专门用来写入的
        row_lists = [create_necessary_table_sql]  # 默认自带建表语句
        for chunk_dataframe in pd.read_sql(select_file_content_sql, conn, chunksize=100):
            for index, row in chunk_dataframe.iterrows():  # 每次对这个进行处理
                data = dict(row)

                try:
                    one_project = data.get("content")
                    need_keys = {'doors', "nodes", "rooms", "walls"}
                    key_union = set(one_project.get("layout_unit").keys()) & need_keys
                    if key_union != need_keys:
                        raise FeatureDictKeyError(
                            f"dict don't have the necessary keys. now just have{key_union} need {need_keys}")
                except Exception:
                    continue
                feature = FeatureProcess()
                try:
                    result = feature.parse_to_remote_compute_plan_graph(data)
                    dict_data = asdict(result)
                    sql = insert_new_plan_graph_dim_sql.format(
                        id=dict_data['id'],
                        plan_area=dict_data['plan_area'],
                        plan_name=dict_data['plan_name'],
                        plan_l=dict_data['plan_l'],
                        plan_w=dict_data['plan_w'],
                        bedroom_l=dict_data['bedroom_l'],
                        bedroom_w=dict_data['bedroom_w'],
                        bedroom_x=dict_data['bedroom_x'],
                        bedroom_y=dict_data['bedroom_y'],
                        livingroom_l=dict_data['livingroom_l'],
                        livingroom_w=dict_data['livingroom_w'],
                        livingroom_x=dict_data['livingroom_x'],
                        livingroom_y=dict_data['livingroom_y'],
                        entrance_x=dict_data['entrance_x'],
                        entrance_y=dict_data['entrance_y']
                    )

                    # 判断和插入数据
                    row_lists.append(sql)
                    if len(row_lists) >= 100:
                        print(row_lists)
                        insert_into_new_dim(" ".join(row_lists))
                        row_lists = []
                except FeatureDictKeyError:
                    print("跳过这个，缺少字段的")
                except Exception as e:
                    print(e)  # 如果是失败的
                    failed_id_list.append(dict_data['id'])  # 错误的记录下来

        if len(row_lists) != 0:
            insert_into_new_dim(" ".join(row_lists))
    print(len(failed_id_list))
    print(failed_id_list)


if __name__ == '__main__':
    # main()  # 这个是处理中间值的
    # 这儿有22827条数据
    now = time.time()
    start_new_process()  # 这个是对应新的维度表的处理
    print(f"total_spend_time {time.time()-now}")