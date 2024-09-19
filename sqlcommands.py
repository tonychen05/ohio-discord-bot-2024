#file to type sql commands in to manipulate database

import sqlite3
conn = sqlite3.connect('db.sqlite')
cursor = conn.cursor()

#enter sql commands here inside "cursor.execute({sql code})"

conn.commit()