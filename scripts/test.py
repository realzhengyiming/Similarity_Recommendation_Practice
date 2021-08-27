# 这儿要做的事情是触发从 数据库中读取所有的数据到本地（数据流提前处理好的数据）
# todo 可以问的东西
#  1。这个东西未来不是要给我们接管了吗，那么airflow也可以接入了，默认的一些预计算的东西也可以放在这个仓库做成服务。
#  2。或者这一层
#  3。这个服务给运维管理吗


import pickle
# 先是直接复制数据进来
data_list = pickle.load(open('need_data.pkl', 'rb'))

print(len(data_list))
# print(data_list[0])

need_data_list = []
a = set()
count = 1
for one_line in data_list:
    # print(one_line)
    # if one_line.get("file_type")=="RESIDENTIAL_UNIT":
    #     need_data_list.append(one_line)
    print(one_line)
    if count == 2:
        break
    count += 1
