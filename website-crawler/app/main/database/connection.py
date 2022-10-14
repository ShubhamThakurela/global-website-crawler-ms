from app.main.database.connector import db_connection, CREDENTIALS


def prepare_update(data_dict, data_id):
    expression = ""
    data_tuple = ()
    for key, value in data_dict.items():
        data_tuple = data_tuple + (value,)
        expression += key + "=%s, "

    data_tuple = data_tuple + (data_id,)
    return data_tuple, expression.strip(", ")


def prepare_insert(data_dict):
    expression_col = ""
    expression_val = ""
    data_tuple = ()
    for key, value in data_dict.items():
        data_tuple = data_tuple + (value,)
        expression_col += key + ", "
        expression_val += "%s, "

    return data_tuple, expression_col.strip(", "), expression_val.strip(", ")


def insert_update_scraping_detail(data_dict):
    try:
        connection = db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT sd_id FROM {}.scraping_detail WHERE web_url='{}'".format(CREDENTIALS['DATABASE'], data_dict['web_url']))
        s_detail = cursor.fetchone()
        if s_detail:
            sd_id = s_detail[0]
            update_data, expression = prepare_update(data_dict, sd_id)
            query = "UPDATE " + CREDENTIALS['DATABASE'] + ".scraping_detail SET " + expression + " WHERE sd_id=%s"
            cursor.execute(query, update_data)
        else:
            insert_data, expression_col, expression_val = prepare_insert(data_dict)
            query = "INSERT INTO " + CREDENTIALS['DATABASE'] + ".scraping_detail (" + expression_col + ") VALUES (" + expression_val + ")"
            cursor.execute(query, insert_data)
            sd_id = cursor.lastrowid
        connection.commit()
        connection.close()
        return sd_id
    except Exception as e:
        print(str(e))
        return None
