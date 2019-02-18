import psycopg2
import subprocess
from configparser import ConfigParser
import os
import psycopg2
from operator import itemgetter

def countRow(tableName,cursor): # return integer of table row
	command = 'SELECT COUNT(*) FROM ' + tableName + ';'
	cursor.execute(command)
	return cursor.fetchone()[0]



def insertDataSubscriber(idNum,uId,sourceType,cursor): #function to insert new customer data
    cursor.execute ("select max(id) from subscribers;")
    maxId = cursor.fetchone()[0]
    if maxId:
        maxId +=1
    else:
        maxId = 1
    cursor.execute("INSERT INTO subscribers (id,uid,type) VALUES (%s, '%s', '%s');" % (maxId, uId, sourceType))

def connect(): #function to provide connection
    """ Connect to the PostgreSQL database server """
    conn = None
    # connect to the PostgreSQL server
    print('Connecting to the PostgreSQL database...')
    DATABASE_URL = os.environ['DATABASE_URL']
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn
        
    