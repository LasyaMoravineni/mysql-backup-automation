from datetime import datetime
import json
import os
import sys
import logging
import getpass
import mysql.connector




db_user = os.getenv("DB_USER", "root")
db_host = os.getenv("DB_HOST", "localhost")
db_password = getpass.getpass("Enter MySQL password: ")


# Logging setup
logging.basicConfig(
    filename="backup_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)



#Loading json data and error handling
try:
    with open("backup_config.json") as f:
       config=json.load(f)

    backup_type=config.get("backup_type")
    tables_to_backup =config.get("tables",[])

    if not backup_type or not isinstance(tables_to_backup, list):
        raise ValueError("Invalid JSON structure")


except Exception as e:
    logging.error(f"Invalid JSON data: {e}")
    print(f"Invalid JSON data: {e}")
    sys.exit(1)



#Start
start_time = datetime.now()
logging.info(f"Backup started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Backup started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")



#Connecting to mysql
conn=mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_password
)
cursor=conn.cursor()




#Determining backup type
try:
    final_tables=[]

    if backup_type.lower()=="full":
        db_names = {t.split(".")[0] for t in tables_to_backup}
        for db in db_names:
            cursor.execute(f"SHOW TABLES FROM {db};")
            all_tables=cursor.fetchall()

            for t in all_tables:
                if "_backup" not in t[0]:   #Exclude already backed-up tables
                    final_tables.append(f"{db}.{t[0]}")
    
    elif backup_type.lower()=="custom":
        final_tables=tables_to_backup
    else:
        raise ValueError("Could not determine backup_type")
    
except Exception as e:
    print(f"Error determining tables: {e}")
    logging.error(f"Error determining tables: {e}")
    sys.exit(1)




#Backup query
for table in final_tables:
    try:
        db_name, table_name=table.split(".")
        timestamp=datetime.now().strftime("%Y%m%d%H%M%S")
        backup_table=f"{table_name}_backup{timestamp}"

        query=f"CREATE TABLE {db_name}.{backup_table} AS SELECT * FROM {db_name}.{table_name};"

        cursor.execute(query)

        logging.info(f"Backup created for {db_name}.{backup_table}")
        print(f"Backup created: {db_name}.{backup_table}")

    except mysql.connector.Error as err:
        logging.error(f"Failed to back up {table}: {err}")
        print(f"Failed to back up {table}: {err}")
        

#Finish
conn.commit()
cursor.close()
conn.close()


end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

logging.info(f"Backup process completed successfully at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Backup process completed successfully at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

logging.info(f"Total time taken: {duration:.2f} seconds")
print(f"Total time taken: {duration:.2f} seconds")
