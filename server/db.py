import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

class DB:
    def __init__(self):
        self.db = psycopg2.connect(
            database = os.getenv("DATABASE"),
            host = os.getenv("HOST"),
            user = os.getenv("USER"),
            password = os.getenv("PASSWORD"),
            port = os.getenv("PORT")
        )
        self.cursor = self.db.cursor()
        self.create_table()

    def create_table(self):
        query = """CREATE TABLE IF NOT EXISTS wins (
            username VARCHAR(255) PRIMARY KEY,
            wins INTEGER NOT NULL,
            losses INTEGER NOT NULL
        );"""
        callback = lambda: self.cursor.execute(query)
        self.execute(callback)
    
    def execute(self, callback):
        try:
            callback()
            self.db.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: {error}")
    
    def increase_wins(self, username):
        query = """
        WITH upsert AS (
            UPDATE wins 
            SET wins = wins + 1
            WHERE username = %s
            RETURNING *
        )
        INSERT INTO wins (username, wins, losses) 
        SELECT %s, 1, 0
        WHERE NOT EXISTS (SELECT 1 FROM upsert);"""
        callback = lambda: self.cursor.execute(query, (username, username))
        self.execute(callback)
    
    def increase_losses(self, username):
        query = """
        WITH upsert AS (
            UPDATE wins 
            SET losses = losses + 1
            WHERE username = %s
            RETURNING *
        )
        INSERT INTO wins (username, wins, losses) 
        SELECT %s, 0, 1
        WHERE NOT EXISTS (SELECT 1 FROM upsert);"""
        callback = lambda: self.cursor.execute(query, (username, username))
        self.execute(callback)

    def get_user_stats(self, username):
        query = """SELECT wins, losses
                    FROM wins
                    WHERE username = %s;"""
        self.cursor.execute(query, (username, ))
        result = self.cursor.fetchone()  # fetchone() retrieves one record
        if result is not None:
            return {'wins': result[0], 'losses': result[1]}
        else:
            return {'wins': 0, 'losses': 0}
    
    def __del__(self):
        self.cursor.close()
        self.db.close()