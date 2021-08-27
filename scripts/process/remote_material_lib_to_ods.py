import json
import pickle

from scripts.db_dao import local_db_instance


# TODO 20210827(zym)这儿到时候看方案，是主动更新还是被动更新，再来调整这一层的导入是远程还是本地直接操作


def main():
    #
    # sql = "select * from file_content where file_type='RESIDENTIAL_UNIT'"
    # result = db_controller.query_all(sql)
    # import pickle as pkl
    #
    # pkl.dump(result, open('need_data.pkl', 'wb'))
    result = pickle.load(open('../need_data.pkl', 'rb'))

    for i in result:
        json_data = json.dumps(i).replace("'", "''")
        sql_template = f"insert into ods_file_content (row_data, create_time) values ('{json_data}', '2021-08-27T14:45:00')"
        local_db_instance.insert_data(sql_template)


if __name__ == '__main__':
    main()
    print("finish!")
