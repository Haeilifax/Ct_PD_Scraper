import sqlite3
import os
import ast
import sys
import json
import re
from datetime import date

#MAKE CONTEXT MANAGERS FOR DATABASES
#OR MAKE DATABASE CONNECTION SEPERATE

def get_date(file_name):
    pattern = r"[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}"
    date = re.search(pattern, file_name).group()
    return date
    
def extract_data(data_file):
    with open(data_file, "r") as f:
        if data_file.endswith(".txt"):
            text = f.read()
            data = ast.literal_eval(text)
        elif data_file.endswith(".json"):
            data = json.load(f)    
        else:
            raise TypeError("Expected file of type .txt or .json")
    return data

def get_inserter(variety, **kwargs):
    if (cased:=variety.lower()) == "basic":
        return Basic_Inserter(**kwargs)
    elif cased == "testing":
        return Inserter(**kwargs)

#needs to be made more modular
class Inserter():
    def __init__(self, database):
        # self.person = {
        #     "first": "", "last": "", "age": "", "st_add": "", "city": ""
        #     }
        # self.crime = {"name": ""}
        # self.arrest = {"location": "", "date": "", "p_id": ""}
        # self.count_crime = {"count": "", "c_id": "", "p_id": "", "a_id":""}
        # self.conn = database_connect(database)
        self.database = database
        self.c_id = []
        self.count = []

    def database_connect(self):
        if os.path.exists(self.database):
            try:
                conn = sqlite3.connect(self.database)
                self.conn = conn
            except sqlite3.Error as e:
                print(e)
        else:
            raise IOError("Database not found")

    def _insert_person(self, first, last, age, st_add, city):
        cur = self.conn.cursor()
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
        self.p_id = cur.lastrowid

    def _insert_crime(self, name):
        cur = self.conn.cursor()
        exist_sql = "SELECT crime_name FROM scrape_crime WHERE crime_name = :name"
        value = {"name": name}
        cur.execute(exist_sql, value)
        _crimes = cur.fetchone()
        if _crimes:
            self.c_id.append(_crimes[0])
        else:
            sql = "INSERT INTO scrape_crime (crime_name) VALUES (:name)"
            cur.execute(sql, value)
            self.c_id.append(name)

    def _insert_arrest(self, location, date):
        cur = self.conn.cursor()
        sql = """
        INSERT INTO
        scrape_arrest (location, date, person_id) 
        VALUES (:location, :date, :p_id)
        """
        values = {
            "location": location,
            "date": date,
            "p_id": self.p_id
            }
        cur.execute(sql, values)
        self.a_id = cur.lastrowid

    def _insert_count_crime(self, index):
        cur = self.conn.cursor()
        sql = """
        INSERT INTO 
        scrape_crime_count (count, crime_id, person_id, arrest_id_id) 
        VALUES (:count, :c_id, :p_id, :a_id)
        """
        values = {
            "count": self.count[index],
            "c_id": self.c_id[index],
            "p_id": self.p_id,
            "a_id": self.a_id
        }
        cur.execute(sql, values)

    def insert(self, data_file="clean_2019-11-13.txt"):
        """Takes cleaned arrest file and inserts into database"""   
        base_date = get_date(data_file)
        data = extract_data(data_file)
        for _, arrest in data.items():
            pdcity = "Unknown"
            if _ == "pd_city":
                pdcity = arrest
                continue
            if len(full_name:= arrest["name"].split()) == 2:
                first_name, last_name = full_name
            elif len(full_name) == 3:
                #inserting middle_name is unimplemented currently
                first_name, middle_name, last_name = full_name
            else:
                raise AssertionError("name of arrestee incorrect format")
            age = arrest["age"]
            #quick sanity check
            assert isinstance(age, int)
            if len(address:= arrest["address"].split(", ")) > 1:
                st_add = address[0]
                city = address[1]
            else:
                st_add = address[0]
                city = pdcity
            self._insert_person(first_name, last_name, age, st_add, city)
            for crime in (crimes:= arrest["crimes"]):
                self.count.append(crime[0])
                self._insert_crime(crime[1])
            date = arrest.get("date", base_date)
            self._insert_arrest(city, date)
            assert len(self.count) == len(self.c_id)
            for index in range(0, len(self.count)):
                self._insert_count_crime(index)
        self.conn.commit()
        self.conn.close()

class Basic_Inserter():
    def __init__(self, database):
        self.database = database

    def __enter__(self):
        self.database_connect()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.database_close()

    def database_connect(self):
        if os.path.exists(self.database):
            try:
                conn = sqlite3.connect(self.database)
                self.conn = conn
            except sqlite3.Error as e:
                print(e)
        else:
            raise IOError("Database not found")

    def _insert_name(self, first_name, last_name):
        cur = self.conn.cursor()
        sql = """
        INSERT INTO person (first_name, last_name)
        VALUES (:first_name, :last_name)
        """
        values = {
            "first_name" : first_name,
            "last_name" : last_name
        }
        cur.execute(sql, values)
        self.p_id = cur.lastrowid

    def _insert_content(self, content):
        cur = self.conn.cursor()
        sql = """
        INSERT INTO content (person_id, content, date) 
        VALUES (:person_id, :content, :date)
        """
        values = {
            "person_id" : self.p_id,
            "content" : content,
            "date" : self.date
        }
        cur.execute(sql, values)

    def insert(self, data, date=date.today()):
        if not self.conn:
            raise Exception("Connect to a database")
        self.date = date
        for _, arrest in data.items():
            print(_, arrest)
            #pd_city not yet implemented
            if _ == "pd_city":
                continue
            full_name = arrest["name"].split()
            first_name = full_name[0]
            last_name = full_name[-1]
            self._insert_name(first_name, last_name)
            content = arrest["content"]
            self._insert_content(content)
        self.conn.commit()

    def database_close(self):
        self.conn.close()

    def insert_from_file(self, data_file):
        self.date = get_date(data_file)
        data = extract_data(data_file)
        self.insert(data, self.date)

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
    VALUES (:location, :date, :p_id)
    """
    values = {
        "location": location,
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
    values = {
        "count": count,
        "c_id": crime_id,
        "p_id": person_id,
        "a_id": arrest_id
    }
    cur.execute(sql, values)

def start_insertion(db_file="db.sqlite3", data_file="clean_2019-11-13.txt"):
    conn = database_connect(db_file)
    with open(data_file, "r") as f:
        if data_file.endswith(".txt"):
            text = f.read()
            data = ast.literal_eval(text)
            base_date = data_file[6:-4]
        elif data_file.endswith(".json"):
            data = json.load(f)
            base_date = data_file[6:-5]
    
    for _, arrest in data.items():
        if _ == "pdcity":
            continue
        first_name, last_name = arrest["name"].split(" ")
        age = arrest["age"]
        address = arrest["address"].split(", ")
        if len(address) > 1:
            st_add = address[0]
            city = address[1]
        else:
            st_add = address[0]
            try:
                city = data["pd_city"]
            except KeyError:
                city = "Unknown"
        crimes = arrest["crimes"]
        p_id = insert_person(conn, first_name, last_name, age, st_add, city)
        c_id = []
        count = []
        for crime in crimes:
            count.append(crime[0])
            c_id.append(insert_crime(conn, crime[1]))
        try:
            date = arrest["date"]
        except KeyError:
            date = base_date
        a_id = insert_arrest(conn, city, date, p_id)
        for num, id in zip(count, c_id):
            if isinstance(id, str):
                insert_count_crime(conn, num, id, p_id, a_id)
            elif isinstance(id, tuple):
                insert_count_crime(conn, num, id[0], p_id, a_id)
            else:
                raise TypeError(
                f"id should be of type tuple or string, not {type(id)}"
                )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    start_insertion()