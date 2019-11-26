import sqlite3
import os
import ast
import sys

def database_connect(db_file):
    if os.path.exists(db_file):
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except sqlite3.Error as e:
            print(e)

def insert_person(conn, first, last, age, st_add, city):
    cur = conn.cursor()
    sql = """
            INSERT INTO 
            scrape_person (first_name, last_name, age, street_address, city) VALUES (:first, :last, :age, :st_add, :city)
            """
    values = {
        "first": first, 
        "last": last, 
        "age": age, 
        "st_add": st_add, 
        "city": city
        }
    cur.execute(sql, values)
    return cur.lastrowid

def insert_crime(conn, name):
    cur = conn.cursor()
    exist_sql = "SELECT crime_name FROM scrape_crime WHERE crime_name = :name"
    value = {"name": name}
    cur.execute(exist_sql, value)
    _crimes = cur.fetchall()
    if _crimes:
        return _crimes[0]
    else:
        sql = "INSERT INTO scrape_crime (crime_name) VALUES (:name)"
        cur.execute(sql, value)
        return name

def insert_arrest(conn, location, date, person_id):
    cur = conn.cursor()
    sql = """
    INSERT INTO
    scrape_arrest (location, date, person_id) 
    VALUES (:loc, :date, :p_id)
    """
    values = {
        "loc": location,
        "date": date,
        "p_id": person_id
        }
    cur.execute(sql, values)
    return cur.lastrowid

def insert_count_crime(conn, count, crime_id, person_id, arrest_id):
    cur = conn.cursor()
    sql = """
    INSERT INTO 
    scrape_crime_count (count, crime_id, person_id, arrest_id_id) 
    VALUES (:count, :c_id, :p_id, :a_id)
    """
    print(type(crime_id))
    values = {
        "count": count,
        "c_id": crime_id,
        "p_id": person_id,
        "a_id": arrest_id
    }
    print(type(crime_id))
    cur.execute(sql, values)

def start_insertion(db_file="db.sqlite3", data_file="clean_2019-11-13.txt"):
    conn = database_connect(db_file)
    date = data_file[6:-4]
    with open(data_file, "r") as f:
        text = f.read()
        data = ast.literal_eval(text)
        comment_index = text.index("#")
        pd_city = text[comment_index+1:]
    for _, arrest in data.items():
        first_name, last_name = arrest["name"].split(" ")
        age = arrest["age"]
        address = arrest["address"].split(", ")
        if len(address) > 1:
            st_add = address[0]
            city = address[1]
        else:
            st_add = address[0]
            city = pd_city
        crimes = arrest["crimes"]
        p_id = insert_person(conn, first_name, last_name, age, st_add, city)
        c_id = []
        count = []
        for crime in crimes:
            count.append(crime[0])
            c_id.append(insert_crime(conn, crime[1]))
        a_id = insert_arrest(conn, pd_city, date, p_id)
        for num, id in zip(count, c_id):
            if isinstance(id, str):
                insert_count_crime(conn, num, id, p_id, a_id)
            elif isinstance(id, tuple):
                insert_count_crime(conn, num, id[0], p_id, a_id)
            else:
                raise Exception
    conn.commit()
    conn.close()

if __name__ == "__main__":
    start_insertion()