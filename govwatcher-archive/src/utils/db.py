"""
Database connection and utility functions for the archive system.
"""
import psycopg2
import psycopg2.extras
import logging

logger = logging.getLogger('govwatcher-archive.db')

class Database:
    """PostgreSQL database connection manager"""
    
    def __init__(self, host, port, database, user, password):
        """Initialize database connection"""
        self.conn_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.conn = None
        self.connect()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            logger.info("Database connection established")
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def get_connection(self):
        """Get the current database connection"""
        if not self.conn or self.conn.closed:
            self.connect()
        return self.conn
    
    def execute(self, query, params=None, commit=False):
        """Execute a query and return the cursor"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cursor.execute(query, params)
            if commit:
                conn.commit()
            return cursor
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            logger.debug(f"Query: {query}, Params: {params}")
            raise
    
    def query_one(self, query, params=None):
        """Execute a query and return a single result"""
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def query_all(self, query, params=None):
        """Execute a query and return all results"""
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def insert(self, table, data, returning='id'):
        """Insert data into a table and return the specified column"""
        columns = data.keys()
        values = [data[column] for column in columns]
        placeholders = [f"%({col})s" for col in columns]
        
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        if returning:
            query += f" RETURNING {returning}"
        
        cursor = self.execute(query, data, commit=True)
        if returning:
            result = cursor.fetchone()
            return result[0] if result else None
        return None
    
    def update(self, table, data, condition, condition_params=None):
        """Update data in a table based on a condition"""
        if not data:
            return 0
        
        set_clauses = [f"{column} = %({column})s" for column in data.keys()]
        params = data.copy()
        
        if condition_params:
            params.update(condition_params)
        
        query = f"""
            UPDATE {table}
            SET {', '.join(set_clauses)}
            WHERE {condition}
        """
        
        cursor = self.execute(query, params, commit=True)
        return cursor.rowcount
    
    def delete(self, table, condition, params=None):
        """Delete rows from a table based on a condition"""
        query = f"DELETE FROM {table} WHERE {condition}"
        cursor = self.execute(query, params, commit=True)
        return cursor.rowcount
    
    def transaction(self):
        """Context manager for database transactions"""
        return Transaction(self)

class Transaction:
    """Context manager for database transactions"""
    
    def __init__(self, db):
        self.db = db
        self.conn = None
    
    def __enter__(self):
        self.conn = self.db.get_connection()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # No exception occurred, commit the transaction
            self.conn.commit()
        else:
            # Exception occurred, rollback the transaction
            self.conn.rollback()
            logger.error(f"Transaction rolled back due to: {exc_val}")
        
        return False  # Don't suppress exceptions 