# ml_template

## Intro
基于机器学习最基础的应用场景之一,相似性判断。使用户型图，提取出客厅，卧室等的相对位置和外围envolop的长款（shapley）
作为特征，然后使用最短距离，求他们之间的相似程度。

## 使用方法
项目内目录下创建config.ini，并且填上自己存放维度数据的数据库
```
[data_warehouse]
PG_HOST=xxxxx
PG_USER=xxx
PG_PASSWORD=xx
PG_DBNAME=xxx
PG_PORT=5435
```


打包docker镜像
cmd进入到项目文件夹内，执行创建容器
"." 代表当前目录
```
docker build -t ai_server_learn:test . 
```

运行docker服务

```docker run --name ai_test -p 5000:5000 ai_server_learn:test```

预测模型

浏览器访问 http://127.0.0.1:5000

借口文档

浏览器访问 http://127.0.0.1:5000/docs

