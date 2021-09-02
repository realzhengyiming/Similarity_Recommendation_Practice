import time
import unittest

from util.process_dataclass import FloorPlanGraph
from models.similar_recommendation import SimilarRecommendation


class TestBuildingTile(unittest.TestCase):

    def test_similar_recommendation(self):
        now = time.time()
        weights = {
            'livingroom_xy_weight': 5,  # 当成默认的配置值
            'livingroom_lw_weight': 5,
            'bedroom_xy_weight': 5,
            'bedroom_wl_weight': 5,
            'plan_graph_wl_weight': 5,
            'entrance_xy_weight': 5
        }
        data = {'id': 140572,
                'plan_graph_area': 82.27,
                'plan_graph_name': '3房1厅-105.35m²-竖厅-Nov10-18857',
                'plan_graph_lw': [10050.0, 9950.0],
                'bedroom_dim_list': [{'long': 3550.0,
                                      'width': 2850.0,
                                      'centroid_position': [-374, 2531]},
                                     {'long': 2600.0,
                                      'width': 2650.0,
                                      'centroid_position': [-2150, -2125]},
                                     {'long': 5250.0,
                                      'width': 3100.0,
                                      'centroid_position': [-3291, 2218]}],
                'livingroom_xy': [2390, -424],
                'livingroom_lw': [8100.0, 6850.0],
                'entrance_xy': [4975, -4277]}

        a = SimilarRecommendation(**weights)
        target_plan = FloorPlanGraph()
        target_plan.parse_from_dict(data)

        result = a.iter_get_min_score(target_plan)  # 查询出score， id ，然后再拼接起来就好了呀。
        print(result)
        print(len(result))
        print(time.time() - now)  # 7s 计算，如果放到内存中那是不是就不用7秒了,还要再经过一个查询，这可真是
        self.assertTrue(result)

