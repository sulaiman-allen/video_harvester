from download_script import db_connect
#import os
#DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'episode_db.sqlite3')

con = db_connect() # connect to the database
cur = con.cursor() # instantiate a cursor obj
customers_sql = """
	CREATE TABLE episodes(
		id integer PRIMARY KEY,
		show_name text NOT NULL,
		url text NOT NULL,
		episode_name text,
		date text)"""
cur.execute(customers_sql)
