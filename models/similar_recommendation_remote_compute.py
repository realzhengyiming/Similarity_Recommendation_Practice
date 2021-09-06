from dataclasses import asdict
from typing import Dict

# 这个版本是线上计算的版本，只需要处理成线上参数传递上去就可以了
import pandas as pd

from constant import select_compute_sql
from models.feature_process import FeatureProcess
from util.dataclasses import FeatureWeight
from util.db import data_session_instance


class SimilarRecommendation:  # 可以，但是很难看
    def _get_real_weight(self, n: int):  # 权重按照1到max int进行映射，只能输入10个值，映射的函数
        if n == 0:
            raise Exception(f"the range of n is 1~{self.max_weight}!")
        weight = self.max_weight + 1 - n
        return weight

    def train_and_predict(self, json_data: Dict, weight_data: Dict):  # 传进来的这个东西要检查
        '''
        1. 传进来的是一个户型的json数据
        2. 和户型这几个因素的权重数据  todo 权重数据可能还需要进行一定的调整
        :param remote_compute_plangraph:
        :return:
        '''
        feature_weight_dict = asdict(self._get_total_real_weight(**weight_data))
        feature = FeatureProcess()
        remote_plan_graph = feature.parse_to_remote_compute_plan_graph_by_json(json_data)
        data = asdict(remote_plan_graph)
        sql = select_compute_sql.format(
            plan_l=data['plan_l'],
            plan_w=data['plan_w'],
            bedroom_l=data['bedroom_l'],
            bedroom_w=data['bedroom_w'],
            bedroom_x=data['bedroom_x'],
            bedroom_y=data['bedroom_y'],
            livingroom_l=data['livingroom_l'],
            livingroom_w=data['livingroom_w'],
            livingroom_x=data['livingroom_x'],
            livingroom_y=data['livingroom_y'],
            entrance_x=data['entrance_x'],
            entrance_y=data['entrance_y'],

            plan_lw_weight=feature_weight_dict['plan_lw_weight'],
            bedroom_lw_weight=feature_weight_dict['bedroom_lw_weight'],
            bedroom_xy_weight=feature_weight_dict['bedroom_xy_weight'],
            livingroom_lw_weight=feature_weight_dict['livingroom_lw_weight'],
            livingroom_xy_weight=feature_weight_dict['livingroom_xy_weight'],
            entrance_xy_weight=feature_weight_dict['entrance_xy_weight']
        )
        print(sql)
        # 传值，然后查询出最小分数的结果，打印出来
        result_list = []
        with data_session_instance.get_engine().connect().execution_options(stream_results=True) as conn:
            for chunk_dataframe in pd.read_sql(sql, conn, chunksize=100):
                for index, row in chunk_dataframe.iterrows():  # 每次对这个进行处理
                    data = dict(row)
                    if "id" in data:
                        data['id'] = int(data['id'])
                    print(data)
                    result_list.append(data)
        return result_list

    def _get_total_real_weight(self,
                               livingroom_xy_weight: int = 5,  # 当成默认的配置值
                               livingroom_lw_weight: int = 5,
                               bedroom_xy_weight: int = 5,
                               bedroom_lw_weight: int = 5,
                               plan_lw_weight: int = 5,
                               entrance_xy_weight: int = 5, max_weight=10) -> FeatureWeight:
        '''
        :param livingroom_xy_weight:1~10  权重越大，对这个因素看得越重（评分越小）
        :param livingroom_lw_weight:1~10
        :param bedroom_xy_weight:1~10
        :param bedroom_lw_weight:1~10
        :param plan_graph_wl_weight:1~10
        :param entrance_xy_weight:1~10
        '''

        # 对权重进行正则化处理
        self.max_weight = max_weight

        total_weight = livingroom_xy_weight + livingroom_lw_weight + bedroom_xy_weight + bedroom_lw_weight + plan_lw_weight + entrance_xy_weight

        feature_weight = FeatureWeight()
        feature_weight.livingroom_xy_weight = livingroom_xy_weight / total_weight
        feature_weight.livingroom_lw_weight = livingroom_lw_weight / total_weight
        feature_weight.bedroom_xy_weight = bedroom_xy_weight / total_weight
        feature_weight.bedroom_lw_weight = bedroom_lw_weight / total_weight
        feature_weight.plan_lw_weight = plan_lw_weight / total_weight
        feature_weight.entrance_xy_weight = entrance_xy_weight / total_weight

        return feature_weight


if __name__ == '__main__':
    a = SimilarRecommendation()
    json_data = {"id": 24567,
                 "wkt": "POLYGON ((2200 -3950, -500 -3950, -1550 -3950, -6250 -3950, -6250 -3400, -7100 -3400, -7100 -1850, -6250 -1850, -6250 -800, -6250 50, -7100 50, -7100 2150, -6250 2150, -6250 3200, 50 3200, 50 5300, 2200 5300, 5550 5300, 5550 1850, 5550 -800, 5550 -3950, 2200 -3950))",
                 "main_entrance_wkt": "LINESTRING (750 5300, 1650 5300)", "rooms": [{"id": 2291230,
                                                                                     "wkt": "POLYGON ((-6250 -3950, -6250 -3400, -7100 -3400, -7100 -1850, -6250 -1850, -6250 -800, -1550 -800, -1550 -3950, -6250 -3950))",
                                                                                     "type": 2}, {"id": 2291229,
                                                                                                  "wkt": "POLYGON ((2200 -2050, -500 -2050, -500 -3950, -1550 -3950, -1550 -800, -6250 -800, -6250 50, -7100 50, -7100 2150, -6250 2150, -6250 3200, 50 3200, 50 5300, 2200 5300, 2200 1850, 3250 1850, 3250 -800, 2200 -800, 2200 -2050))",
                                                                                                  "type": 4},
                                                                                    {"id": 2291228,
                                                                                     "wkt": "POLYGON ((2200 -2050, 2200 -3950, -500 -3950, -500 -2050, 2200 -2050))",
                                                                                     "type": 10}, {"id": 2291227,
                                                                                                   "wkt": "POLYGON ((2200 -3950, 2200 -2050, 2200 -800, 3250 -800, 5550 -800, 5550 -3950, 2200 -3950))",
                                                                                                   "type": 3},
                                                                                    {"id": 2291226,
                                                                                     "wkt": "POLYGON ((2200 5300, 5550 5300, 5550 1850, 3250 1850, 2200 1850, 2200 5300))",
                                                                                     "type": 3}, {"id": 2291225,
                                                                                                  "wkt": "POLYGON ((5550 -800, 3250 -800, 3250 1850, 5550 1850, 5550 -800))",
                                                                                                  "type": 7}]}
    feature_weight = FeatureWeight()
    feature_weight.livingroom_xy_weight = 5
    feature_weight.livingroom_lw_weight = 5
    feature_weight.bedroom_xy_weight = 5
    feature_weight.bedroom_wl_weight = 5
    feature_weight.plan_graph_wl_weight = 5
    feature_weight.entrance_xy_weight = 5

    weight_data = asdict(feature_weight)
    a.train_and_predict(json_data, weight_data)
