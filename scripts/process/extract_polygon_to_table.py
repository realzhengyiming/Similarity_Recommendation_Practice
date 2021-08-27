## 这一层是通过预先处理，提取出各个类似之前json的样式，提取出对应的polygon
from scripts.db_dao import local_db_instance

with local_db_instance.cursor as cursor:
    cursor.itersize = 1000
    query = "select * from ods_file_content limit 2000"
    cursor.execute(query)
    for row in cursor:
        print(row)