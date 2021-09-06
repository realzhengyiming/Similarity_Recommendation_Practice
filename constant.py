CONFIG_PATH = "config.ini"

# sql
select_file_content_sql = '''
select * from file_content where file_type='RESIDENTIAL_UNIT'
                             and id in (select distinct id from file 
                            where file_type='RESIDENTIAL_UNIT'
                              and folder_id = 1);
'''

create_necessary_table_sql = '''
create extension if not exists postgis;
create table if not exists plan_graph_dim(
    id int,
    plan_graph_area float,
    plan_graph_name text,
    plan_graph_lw jsonb,
    bedroom_dim_list jsonb,
    livingroom_xy jsonb,
    livingroom_lw jsonb,
    entrance_xy jsonb
);

create table if not exists new_plan_dim(
    id int,
    plan_area float,
    plan_name text,
    plan_l float,
    plan_w float,
    bedroom_l float,
    bedroom_w float,
    bedroom_x float,
    bedroom_y float,
    livingroom_l float,
    livingroom_w float,
    livingroom_x float,
    livingroom_y float,
    entrance_x float,
    entrance_y float
);

'''

# todo 我这边新建了一个表，用来测试用的。看看怎么回事
insert_floor_graph_dim_sql = '''
    insert into train_data (id,plan_graph_lw,plan_graph_area,plan_graph_name,bedroom_dim_list,livingroom_xy,
                            livingroom_lw,entrance_xy) values (
                            {id},
                           '{plan_graph_lw}',
                            {plan_graph_area},
                            '{plan_graph_name}',
                            '{bedroom_dim_list}',
                            '{livingroom_xy}',
                            '{livingroom_lw}',
                            '{entrance_xy}');
    '''

insert_new_plan_graph_dim_sql = '''
insert into new_plan_dim (
    id ,plan_area ,plan_name ,plan_l ,plan_w  ,bedroom_l  ,bedroom_w  ,bedroom_x  ,bedroom_y ,livingroom_l  ,livingroom_w  ,livingroom_x  ,livingroom_y  ,entrance_x  ,
    entrance_y  ) values ({id} ,{plan_area} ,'{plan_name}' ,{plan_l} ,{plan_w}  ,{bedroom_l}  ,{bedroom_w}  ,{bedroom_x}  ,{bedroom_y} ,{livingroom_l}  ,{livingroom_w}  ,
    {livingroom_x}  ,{livingroom_y}  ,{entrance_x}  ,{entrance_y}  );
    '''

# 这儿要做一个什么东西呢
compute_sql = '''
select  id ,
        plan_name ,
        (abs(plan_l - 100) + abs(plan_w - 100) ) * 1 as plan_lw_score,
        (abs(bedroom_l - 100) + abs(bedroom_w - 100) ) * 1 as bedroom_lw_score,
        (abs(bedroom_x - 100) + abs(bedroom_y - 100) ) * 1 as bedroom_xy_score,
        (abs(livingroom_l - 100) + abs(livingroom_w - 100) ) * 1 as livingroom_lw,
        (abs(livingroom_x - 100) + abs(livingroom_y - 100) ) * 1 as livingroom_xy,
        (abs(entrance_x - 100) + abs(entrance_y - 100) ) * 1 as entrance_xy_score 
        from new_plan_dim;
'''

select_floor_graph_dim_sql = '''
select * from plan_graph_dim;
'''

select_compute_sql = '''
select distinct on(total_score) * from (
select id,plan_lw_score,bedroom_xy_score,bedroom_lw_score,livingroom_lw_score,livingroom_xy_score,entrance_xy_score,
        plan_lw_score +
        bedroom_lw_score +
        bedroom_xy_score +
        livingroom_lw_score +
        livingroom_xy_score +
        entrance_xy_score as total_score from (
        
        select  id ,
        plan_name ,
        (abs(plan_l - {plan_l}) + abs(plan_w - {plan_w}) ) * {plan_lw_weight} as plan_lw_score,
        (abs(bedroom_l - {bedroom_l}) + abs(bedroom_w - {bedroom_w}) ) * {bedroom_lw_weight} as bedroom_lw_score,
        (abs(bedroom_x - {bedroom_x}) + abs(bedroom_y - {bedroom_y}) ) * {bedroom_xy_weight} as bedroom_xy_score,
        (abs(livingroom_l - {livingroom_l}) + abs(livingroom_w - {livingroom_w}) ) * {livingroom_lw_weight} as livingroom_lw_score,
        (abs(livingroom_x - {livingroom_x}) + abs(livingroom_y - {livingroom_y}) ) * {livingroom_xy_weight} as livingroom_xy_score,
        (abs(entrance_x - {entrance_x}) + abs(entrance_y - {entrance_y}) ) * {entrance_xy_weight} as entrance_xy_score
        from new_plan_dim 
        -- limit 2
        ) as t 
        )t2 where total_score>0 group by total_score,id,plan_lw_score,bedroom_xy_score,bedroom_lw_score,livingroom_lw_score,
                             livingroom_xy_score,entrance_xy_score order by total_score limit 30
'''  # todo 怎么匹配到自己不是 0 呢 这个问题要看看怎么回事