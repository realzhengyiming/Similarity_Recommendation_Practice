import time
from typing import Dict

import numpy as np
import pandas as pd

from util.db import data_session_instance
from constant import select_floor_graph_dim_sql
from util.process_dataclass import FloorPlanGraph


class SimilarRecommendation:
    def _get_real_weight(self, n: int):  # 权重按照1到max int进行映射，只能输入10个值，映射的函数
        if n == 0:
            raise Exception(f"the range of n is 1~{self.max_weight}!")
        weight = self.max_weight + 1 - n
        return weight

    def iter_get_min_score(self, target_plan: FloorPlanGraph, limit_number=30):  # 这个新的匹配是，去掉了分数相同的东西的
        now = time.time()
        scores_and_id = []
        with data_session_instance.get_engine().connect().execution_options(stream_results=True) as conn:
            for chunk_dataframe in pd.read_sql(select_floor_graph_dim_sql, conn, chunksize=100):
                for index, row in chunk_dataframe.iterrows():  # 每次对这个进行处理
                    data = dict(row)
                    floor_plan_graph = FloorPlanGraph()
                    floor_plan_graph.parse_from_dict(data)
                    score_dict = self._get_plan_similar_scores(target_plan, floor_plan_graph)  # todo 这里面也需要就进行瘦身
                    score = score_dict['total_score']
                    if score == 0.0:  # 找到了完全一样的，可能就是他自己，当然就不要了
                        continue
                    if score not in [i[0] for i in scores_and_id]:
                        scores_and_id.append([score, floor_plan_graph.id, score_dict])

                scores_and_id.sort()  # 分治的思想
                if len(scores_and_id) > limit_number:  # 如果是小于的就没有进行排序了
                    scores_and_id = scores_and_id[:limit_number]

        # return
        print(time.time()-now)
        return

    def __init__(self,
                 livingroom_xy_weight: int = 5,  # 当成默认的配置值
                 livingroom_lw_weight: int = 5,
                 bedroom_xy_weight: int = 5,
                 bedroom_wl_weight: int = 5,
                 plan_graph_wl_weight: int = 5,
                 entrance_xy_weight: int = 5, max_weight=10):
        '''
        :param livingroom_xy_weight:1~10  权重越大，对这个因素看得越重（评分越小）
        :param livingroom_lw_weight:1~10
        :param bedroom_xy_weight:1~10
        :param bedroom_wl_weight:1~10
        :param plan_graph_wl_weight:1~10
        :param entrance_xy_weight:1~10
        '''

        # 对权重进行正则化处理
        self.max_weight = max_weight
        total_weight = self._get_real_weight(livingroom_xy_weight) + self._get_real_weight(
            livingroom_lw_weight) + self._get_real_weight(bedroom_xy_weight) + self._get_real_weight(
            bedroom_wl_weight) + self._get_real_weight(plan_graph_wl_weight) + self._get_real_weight(entrance_xy_weight)
        self.livingroom_xy_weight = self._get_real_weight(livingroom_xy_weight) / total_weight
        self.livingroom_lw_weight = self._get_real_weight(livingroom_lw_weight) / total_weight
        self.bedroom_xy_weight = self._get_real_weight(bedroom_xy_weight) / total_weight
        self.bedroom_wl_weight = self._get_real_weight(bedroom_wl_weight) / total_weight
        self.plan_graph_wl_weight = self._get_real_weight(plan_graph_wl_weight) / total_weight
        self.entrance_xy_weight = self._get_real_weight(entrance_xy_weight) / total_weight

    def _get_plan_similar_scores(self, target_plan, other_plan) -> Dict:
        livingroom_xy_weight = self.livingroom_xy_weight
        livingroom_lw_weight = self.livingroom_lw_weight  # 这个整体的长宽可能就不怎么想管了，或者说给它的权重小一些
        bedroom_xy_weight = self.bedroom_xy_weight
        bedroom_lw_weight = self.bedroom_wl_weight
        plan_graph_lw_weight = self.plan_graph_wl_weight
        entrance_xy_weight = self.entrance_xy_weight

        # 增加客厅与户型图重心之间的相对位置的做差得分
        livingroom_xy_score = livingroom_xy_weight * np.sum(
            np.abs(target_plan.livingroom_xy - other_plan.livingroom_xy))

        plan_lw_score = plan_graph_lw_weight * np.sum(
            np.abs(target_plan.plan_graph_lw - other_plan.plan_graph_lw))
        living_lw_score = livingroom_lw_weight * np.sum(np.abs(target_plan.livingroom_lw - other_plan.livingroom_lw))
        entrance_xy_score = entrance_xy_weight * np.sum(
            np.abs(target_plan.entrance_xy - other_plan.entrance_xy))

        used = set()
        total_score = plan_lw_score + living_lw_score + entrance_xy_score + livingroom_xy_score

        room_total_lw_score = 0
        room_total_xy_score = 0
        for target_index, target_value in enumerate(target_plan.bedroom_dim_list):
            min_score = 1e10  # 这个是设置距离的最大值，最为最小的分数的默认值
            min_score_index = -1
            min_xy_score = 1e10
            min_lw_score = 1e10
            for other_index, other_value in enumerate(other_plan.bedroom_dim_list):  # 这儿也可以进行比对卧室
                if other_index in used:
                    continue

                room_lw_score = bedroom_lw_weight * np.sum(np.abs(target_value[0] - other_value[0]))  # 长款的分数
                room_xy_score = bedroom_xy_weight * np.sum(np.abs(target_value[1] - other_value[1]))  # 这个是位置的分数

                room_j_score = room_lw_score + room_xy_score
                if room_j_score < min_score:
                    min_score = room_j_score
                    min_score_index = other_index

                    min_xy_score = room_xy_score
                    min_lw_score = room_lw_score

            if min_score_index not in used:  # 一轮的最小值
                used.add(min_score_index)  # 配对过一次就不再和下一个进行配对
                total_score += min_score

                room_total_lw_score += min_lw_score
                room_total_xy_score += min_xy_score

        result_data = {
            "plan_lw_score": plan_lw_score,
            "living_lw_score": living_lw_score,
            "entrance_xy_score": entrance_xy_score,
            "livingroom_xy_score": livingroom_xy_score,
            "room_total_lw_score": room_total_lw_score,
            "room_total_xy_score": room_total_xy_score,

            "total_score": total_score
        }
        return result_data
