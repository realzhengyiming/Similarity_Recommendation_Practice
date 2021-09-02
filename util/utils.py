import pandas as pd

from util.db import data_session_instance
from util.process_dataclass import FloorPlanGraph


def random_get_one_home_train_data() -> FloorPlanGraph:
    with data_session_instance.get_engine().connect().execution_options(stream_results=True) as conn:
        for chunk_dataframe in pd.read_sql("select * from plan_graph_dim limit 100", conn, chunksize=100):
            for i, row in chunk_dataframe.sample(1).iterrows():
                result = dict(row)
                a = FloorPlanGraph()
                a.parse_from_dict(result)
                return a


if __name__ == '__main__':
    result = random_get_one_home_train_data()
    print(result)
