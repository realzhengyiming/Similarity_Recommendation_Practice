from fastapi import FastAPI

from api.controller import random_predict, train_and_predict, latest_train_and_predict
from api.items import PlanDataAndWeight, FeatureWight, PlanJsonAndWeight

app = FastAPI()


@app.get("/")
async def home():
    return {"info": "这个是户型推荐的接口，详细接口内容请访问 /docs"}


# @app.post("/recommendation")
# async def similar_recommendation(plan_data_and_weight: PlanDataAndWeight):
#     result = train_and_predict(plan_data_and_weight.dict())
#     return {"floor_graph": result}


@app.post("/final_recommendation")
def final_recommendation(plan_json_and_weight: PlanJsonAndWeight):
    print(plan_json_and_weight)
    result = latest_train_and_predict(plan_json_and_weight.dict())
    return {"result_list": result}


# @app.post("/test_recommendation")
# async def test_random_recommendation(featurewight: FeatureWight):
#     result = random_predict(weight_dict=featurewight.dict())
#     return {"floor_graph": result}
