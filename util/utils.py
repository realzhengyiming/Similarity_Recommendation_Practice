import numpy as np
import pandas as pd
from shapely.ops import unary_union

from util.db import data_session_instance
from util.dataclasses import PlanGraphDim


def random_get_one_home_train_data() -> PlanGraphDim:
    with data_session_instance.get_engine().connect().execution_options(stream_results=True) as conn:
        for chunk_dataframe in pd.read_sql("select * from plan_graph_dim limit 100", conn, chunksize=100):
            for i, row in chunk_dataframe.sample(1).iterrows():
                result = dict(row)
                a = PlanGraphDim()
                a.parse_from_dict(result)
                return a


def safe_union_polygon_list(geom_list):
    assert len(geom_list) != 0  # 如果图片不等于就会爆出错误，说明矩阵也是5行6列的了
    if len(geom_list) > 1:
        total_geom_wkt = unary_union(geom_list)
    else:
        total_geom_wkt = geom_list[0]
    return total_geom_wkt


def relative_xy_to_npy(centroid, reference_centroid):
    result = np.array([centroid.x, centroid.y], np.int16) - np.array([reference_centroid.x, reference_centroid.y],
                                                                     np.int16)
    result = [int(i) for i in list(result)]
    return result


if __name__ == '__main__':
    result = random_get_one_home_train_data()
    print(result)
