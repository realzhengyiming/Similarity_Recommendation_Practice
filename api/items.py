from typing import List

from pydantic import BaseModel
from shapely.geometry import Polygon


class PlanDataClass(BaseModel):
    id: int
    plan_graph_area: float
    plan_graph_name: str
    plan_graph_lw: List
    bedroom_dim_list: List  # 有多个
    livingroom_lw: List
    livingroom_xy: List
    entrance_xy: List  # 门的相对位置


class FeatureWight(BaseModel):
    livingroom_xy_weight: int  # 当成默认的配置值
    livingroom_lw_weight: int
    bedroom_xy_weight: int
    bedroom_lw_weight: int
    plan_lw_weight: int
    entrance_xy_weight: int


class PlanDataJson(BaseModel):
    id: int
    wkt: str
    main_entrance_wkt: str
    rooms: List

class PlanJsonAndWeight(BaseModel):
    plan_json: PlanDataJson
    feature_weight: FeatureWight


class PlanDataAndWeight(BaseModel):
    plan_data_class: PlanDataClass
    feature_weight: FeatureWight
