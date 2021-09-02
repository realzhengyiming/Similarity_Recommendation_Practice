CONFIG_PATH = "config.ini"

# sql
select_file_content_sql = '''
SELECT * FROM file_content where file_type='RESIDENTIAL_UNIT';
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

'''

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

select_floor_graph_dim_sql = '''
select * from plan_graph_dim;
'''
