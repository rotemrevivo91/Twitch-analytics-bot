import mysql.connector
import sys

class Sql():
    
    def __init__(self, database, user, passwd):
        try:
            self.create_db(database,user,passwd)
            self.db = mysql.connector.connect(host="127.0.0.1",  user=user,  passwd=passwd, database=database)
            self.mycursor = self.db.cursor(buffered=True)
        except:
            print('No connection to SQL server could be made. Please turn on your SQL server and try again..')
            sys.exit()
    
    #create database (called upon on first run)
    def create_db(self, database, user, passwd):
        db = mysql.connector.connect(host="127.0.0.1",  user=user,  passwd=passwd)
        mycursor = db.cursor(buffered=True)
        mycursor.execute("SHOW DATABASES")
        for x in mycursor:
            if(x[0] == database):
                return
        mycursor.execute("CREATE DATABASE "+database)
    
    #create table if not exist
    def create_table(self, name, values):
        self.mycursor.execute("SHOW TABLES")
        if(self.mycursor.rowcount == 0):
            self.mycursor.execute("CREATE TABLE "+name+" "+values)
            return
        for x in self.mycursor:
            if(x[0] == name):
              self.mycursor.execute("DROP TABLE "+name)  
        self.mycursor.execute("CREATE TABLE "+name+" "+values)
    
    def insert(self, table, options, values):
        sql = 'INSERT INTO '+table+' '+options+' VALUES '+str(values)
        self.mycursor.execute(sql)
        self.db.commit()
    
    #options - WHERE ()
    def select(self, table, columns, options):
        sql = 'SELECT '+columns+' FROM '+table+' '+options
        self.mycursor.execute(sql)
        return self.mycursor.fetchall()
    
    #update a row in a table where cloumn = value
    def update(self,table,columns,values,column,value):
        sql = 'UPDATE '+table+' SET '+columns+' WHERE '+column+' = '+value
        self.mycursor.execute(sql,values)
        self.db.commit()   
    
    #if table is empty set session=1
    def exist(self,table):
        sql = 'SELECT COUNT(*) FROM '+table
        self.mycursor.execute(sql)
        data = self.mycursor.fetchone()
        #first row in the table session number
        if(data[0] == 0):
            self.insert(table,'(name, session)',('session', 1))
            return False