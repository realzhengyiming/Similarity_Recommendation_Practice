# 主要逻辑区域
from models.similar_recommendation_local_compute import SimilarRecommendation
from models.similar_recommendation_remote_compute import SimilarRecommendation as NewRecommendation
from util.dataclasses import PlanGraphDim
from util.utils import random_get_one_home_train_data


def random_predict(weight_dict):
    target_plan = random_get_one_home_train_data()  # 随机取一个，这个是用来左侧使用的，做了过滤相同分数的结果处理
    a = SimilarRecommendation(**weight_dict)
    result = a.iter_get_min_score(target_plan)
    return result


def train_and_predict(json_data):
    plan_data = json_data.get('plan_data_class')
    feature_weight = json_data.get("feature_weight")
    target_plan = PlanGraphDim()
    target_plan.parse_from_dict(plan_data)
    a = SimilarRecommendation(**feature_weight)
    result = a.iter_get_min_score(target_plan)
    return result


def latest_train_and_predict(json_data):
    new_recommendation = NewRecommendation()

    plan_data = json_data.get('plan_json')
    feature_weight = json_data.get("feature_weight")

    result_list = new_recommendation.train_and_predict(json_data=plan_data, weight_data=feature_weight)
    return result_list
