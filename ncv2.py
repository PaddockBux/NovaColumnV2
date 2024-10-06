from mcstatus import JavaServer
from datetime import datetime
import concurrent.futures
import configparser
import threading
import argparse
import logging
import mariadb
import mcuuid
import queue
import time
import json
import os

def initialize_arguments():
    parser = argparse.ArgumentParser(
    description='''
               _   __                 ______      __                    _    _____ 
              / | / /___ _   ______ _/ ____/___  / /_  ______ ___  ____| |  / /__ \\
             /  |/ / __ \\ | / / __ `/ /   / __ \\/ / / / / __ `__ \\/ __ \\ | / /__/ /
            / /|  / /_/ / |/ / /_/ / /___/ /_/ / / /_/ / / / / / / / / / |/ // __/ 
           /_/ |_/\\____/|___/\\__,_/\\____/\\____/_/\\__,_/_/ /_/ /_/_/ /_/|___//____/ 
                                        NovaColumn V2
          Programmed by & main ideas guy: GoGreek    ::    Co-ideas guy: Draxillian
            
       Fair warning, calling the update function will take a while on large databases!
''',
    epilog="Example usage:\n"
           "Verbose\n"
           "    nc2 -v input.json\n"
           "Update the database\n"
           "    nc2 -u\n"
           "Use multiple threads\n"
           "    nc2 -t 10 input.json\n"
           "Change timeout & threads\n"
           "    nc2 -m 2.3 -t 10 input.json\n\n"
           "For more information, check the README file.",
    formatter_class=argparse.RawDescriptionHelpFormatter
)
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('file', nargs='?', type=str, help="The path to the .json file to be parsed.")
    group.add_argument('-u', '--update', action='store_true', help="Ping/Update the current servers in the database. (does not require a file)")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose mode to print detailed logs.")
    parser.add_argument('-t', '--threads', type=int, default="4", help="The amount of threads to process the file with. (4 default)")
    parser.add_argument('-m', '--timeout', type=float, default="0.3", help="The timeout speed for the servers, read the README for more info. (0.3 default)")
    parser.add_argument('-e', '--external', action='store_true', help="Used for when the database is not on the same machine. (only applies for --update)")
    parser.add_argument('-c', '--verify', action='store_true', help="Verify all playernames in the database. (does not require a file)")
    args = parser.parse_args()
    return args

def read_config():
    config = configparser.ConfigParser()
    config.read("novacolumn.conf")
    config_data = {
        'db_name': config.get('database', 'database_name'),
        'db_username': config.get('database', 'username'),
        'db_pass': config.get('database', 'password'),
        'db_host': config.get('database', 'host'),
        'db_port': config.getint('database', 'port')
    }
    return config_data

def connect_to_db(config_data):
    try:
        conn = mariadb.connect(
            user=config_data['db_username'],
            password=config_data['db_pass'],
            host=config_data['db_host'],
            port=config_data['db_port'],
            database=config_data['db_name']
        )
        logger.info(f"Connected to database {config_data['db_name']} on {config_data['db_host']}:{config_data['db_port']}")
        return conn
    except mariadb.Error as e:
        logger.critical(f"Error connecting to MariaDB Platform: {e}")
        exit(1)

def ping_server(ip, port, timeout):
    try:
        serverping = JavaServer.lookup(f"{ip}:{port}", timeout)
        serverstatus = serverping.status()
        data_out = {
            'ip': ip,
            'port': port,
            'ping': serverstatus.latency,
            'version': serverstatus.version.name,
            'players': serverstatus.players.online,
            'usernames': [player.name for player in (serverstatus.players.sample or [])],
            'uuids': [player.id for player in (serverstatus.players.sample or [])],
            'maxplayers': serverstatus.players.max,
            'motd': serverstatus.motd.to_minecraft(),
            'signedmsg': serverstatus.enforces_secure_chat,
            'favicon': serverstatus.icon
        }
        logger.info(f"🗸 {ip}:{port}")
        return True, data_out
    except Exception as e:
        trace = e.__traceback__
        logger.warning(f"𐄂 {ip}:{port}: {e.with_traceback(trace)}")
        return False, ip, port
    
# Save to DB basically.
def db_handler(ping_queue, conn, update):
    if update == False:
        while 1:
            result = ping_queue.get()
            if result == "STOP":
                break
            elif result[0] is False:
                # ping_queue.task_done() # This might break things
                continue
            else:
                data_out = result[1]
            cursor = conn.cursor()
            add_to_db(cursor, data_out)
            ping_queue.task_done()
    else:
        while 1:
            result = ping_queue.get()
            if result == "STOP":
                break
            elif result[0] is False:
                cursor = conn.cursor()
                ip = result[1]
                port = result[2]
                update_db(cursor, ip, port, False)
            else:
                cursor = conn.cursor()
                data_out = result[1]
                add_to_db(cursor, data_out)
            ping_queue.task_done()

def ping_worker(ip, port, timeout, ping_queue):
    result = ping_server(ip, port, timeout)
    ping_queue.put(result)

def update_db(cursor, ip, port, status):
    cursor.execute("SELECT uid FROM ips WHERE address = ?", (ip,))
    ip_uid = cursor.fetchone()[0]
    cursor.execute("SELECT uid FROM main WHERE ip_fk = ? AND port = ?", (ip_uid, port))
    main_uid = cursor.fetchone()[0]
    logger.debug('Saving to online...')
    cursor.execute('''INSERT INTO online (
            main_fk, online, time
        ) 
        VALUES (?, ?, ?)''', (
            main_uid,
            status,
            time.time()
        )
    )
    # cursor.execute("SELECT online FROM online WHERE main_fk = ?", (main_uid,))

def add_to_db(cursor, data_out):
    ip = data_out['ip']
    port = data_out['port']
    try:
        # Check if IP exists
        cursor.execute("SELECT uid FROM ips WHERE address = ?", (ip,))
        request = cursor.fetchone()
        if request is None:
            logger.debug("New IP!")
            cursor.execute("INSERT INTO ips (address) VALUES (?)", (ip,))
            # Remember the VALUES request!
            cursor.execute("SELECT last_insert_id()")
            # (1,)
            ip_uid = cursor.fetchone()[0]
        else:
            logger.debug(f"Old IP! - Already exists in DB with ID {request[0]}")
            cursor.execute("SELECT uid FROM ips WHERE address=?", (ip,))
            ip_uid = cursor.fetchone()[0]
        
        # Check if version exists
        cursor.execute("SELECT uid FROM versions WHERE text = ?", (data_out['version'],))
        request = cursor.fetchone()
        if request is None:
            logger.debug("New version!")
            cursor.execute("INSERT INTO versions (text) VALUES (?)", (data_out['version'],))
            cursor.execute("SELECT last_insert_id()")
            ver_uid = cursor.fetchone()[0]
        else:
            logger.debug(f"Old version! - Already exists in DB with ID {request[0]}")
            cursor.execute("SELECT uid FROM versions WHERE text=?", (data_out['version'],))
            ver_uid = cursor.fetchone()[0]
        
        # Check if MOTD exists
        cursor.execute("SELECT uid FROM motds WHERE text = ?", (data_out['motd'],))
        request = cursor.fetchone()
        if request is None:
            logger.debug("New MOTD!")
            cursor.execute("INSERT INTO motds (text) VALUES (?)", (data_out['motd'],))
            cursor.execute("SELECT last_insert_id()")
            motd_uid = cursor.fetchone()[0]
        else:
            logger.debug(f"Old MOTD! - Already exists in DB with ID {request[0]}")
            cursor.execute("SELECT uid FROM motds WHERE text=?", (data_out['motd'],))
            motd_uid = cursor.fetchone()[0]
        if data_out['favicon'] is None:
            data_out['favicon'] = 'NO_ICON'
        
        # Check if favicon exists
        cursor.execute("SELECT uid FROM icons WHERE data = ?", (data_out['favicon'],))
        request = cursor.fetchone()
        if request is None:
            logger.debug("New icon!")
            cursor.execute("INSERT INTO icons (data) VALUES (?)", (data_out['favicon'],))
            cursor.execute("SELECT last_insert_id()")
            icon_uid = cursor.fetchone()[0]
        else:
            logger.debug(f"Old icon! - Already exists in DB with ID {request[0]}")
            cursor.execute("SELECT uid FROM icons WHERE data=?", (data_out['favicon'],))
            icon_uid = cursor.fetchone()[0]
        
        # Check for playernames and add to array
        playernames = []
        for username, uuid in zip(data_out['usernames'], data_out['uuids']):
            cursor.execute("SELECT uid FROM playernames WHERE username = ?", (username,))
            exist_username = cursor.fetchone()
            if exist_username:
                uid = exist_username[0]
            else:
                cursor.execute("INSERT INTO playernames (username, userid) VALUES (?, ?)", (username, uuid))
                cursor.execute("SELECT last_insert_id()")
                uid = cursor.fetchone()[0]
            
            playernames.append(uid)

        logger.debug('Saving to main...')
        cursor.execute('''INSERT INTO main (
                ip_fk, port, time, playercount, playermax, motd_fk, ver_fk, users_fk, signed, icon_fk, ping
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                ip_uid, 
                port, 
                time.time(), 
                data_out['players'], 
                data_out['maxplayers'], 
                motd_uid,
                ver_uid, 
                str(playernames), 
                data_out['signedmsg'], 
                icon_uid, 
                data_out['ping']
            )
        )
        cursor.execute("SELECT last_insert_id()")
        main_uid = cursor.fetchone()[0]
        logger.debug('Getting last UID from main...')
        
        logger.debug('Saving to online...')
        cursor.execute('''INSERT INTO online (
                main_fk, online, time
            ) 
            VALUES (?, ?, ?)''', (
                main_uid,
                True,
                time.time()
            )
        )
        logger.debug('Done.')

    except Exception as e:
        trace = e.__traceback__
        logger.warning(f"DB query error:\n{e.with_traceback(trace)}")
        if not data_out['favicon']:
            data_out['favicon'] = "NO_ICON"
        logger.warning(f'''
                    
        Server: {ip}:{port}
        Possible causes of this error include:
        Version [{data_out['version']}]
        MOTD snippet: [{data_out['motd'][:16]}]
        Icon snippet: [{data_out['favicon'][64:10:]}]
        Usernames: {data_out['usernames']}  
        UUIDs: {data_out['uuids']}
        ''')

def init_db(conn):
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM ips')
        logger.info('Found tables.')
    except mariadb.Error:
        logger.info('Tables do not exist. Creating tables...')

        cursor.execute("CREATE TABLE ips (uid SERIAL PRIMARY KEY, address INET4)")
        logger.debug('Created table "ips"')
        
        cursor.execute("CREATE TABLE versions (uid SERIAL PRIMARY KEY, text TINYTEXT) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
        logger.debug('Created table "versions"')
        
        cursor.execute("CREATE TABLE playernames (uid SERIAL PRIMARY KEY, username CHAR(128), userid CHAR(36), valid ENUM('true','false','waiting') DEFAULT 'waiting') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
        logger.debug('Created table "playernames"')
        
        cursor.execute("CREATE TABLE motds (uid SERIAL PRIMARY KEY, text VARCHAR(512)) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
        logger.debug('Created table "motds"')
        
        cursor.execute("CREATE TABLE icons (uid SERIAL PRIMARY KEY, data TEXT)")
        logger.debug('Created table "icons"')
        
        cursor.execute('''CREATE TABLE main (
            uid SERIAL PRIMARY KEY,
            ip_fk BIGINT UNSIGNED NOT NULL,
            port MEDIUMINT,
            time DOUBLE,
            playercount MEDIUMINT,
            playermax MEDIUMINT,
            motd_fk BIGINT UNSIGNED NOT NULL,
            ver_fk BIGINT UNSIGNED NOT NULL,
            users_fk JSON,
            signed BOOLEAN,
            icon_fk BIGINT UNSIGNED NOT NULL,
            ping FLOAT,
            FOREIGN KEY (ip_fk) REFERENCES ips(uid),
            FOREIGN KEY (motd_fk) REFERENCES motds(uid),
            FOREIGN KEY (ver_fk) REFERENCES versions(uid),
            FOREIGN KEY (icon_fk) REFERENCES icons(uid)
        )''')
        logger.debug('Created table "main"')

        cursor.execute('CREATE INDEX idx_ip_port ON main (ip_fk, port)')
        cursor.execute('CREATE INDEX idx_uid ON main (uid)')
        logger.debug('Created main table composite index for ip_fk, port, and uid.')

        cursor.execute('''CREATE TABLE online (
            main_fk BIGINT UNSIGNED NOT NULL, 
            online BOOLEAN NOT NULL DEFAULT TRUE,
            time DOUBLE,
            FOREIGN KEY (main_fk) REFERENCES main(uid)
        )''')
        logger.debug('Created table "online"')
        
        cursor.execute('CREATE TABLE blacklist (address INET4, port MEDIUMINT)')
        logger.debug('Created table "blacklist"')
        
        conn.commit()
        logger.info('Tables created and initialized successfully.')

def main(json_data, max_workers):
    ping_queue = queue.Queue()

    config_data = read_config()
    conn = connect_to_db(config_data)
    init_db(conn)

    db_thread = threading.Thread(target=db_handler, args=(ping_queue, conn, False))
    db_thread.start()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for index in range(len(json_data)):
            # Format: {scan_data[INDEX]['ip']}:{scan_data[INDEX]['ports'][0]['port']}
            executor.submit(ping_worker, json_data[index]['ip'], json_data[index]['ports'][0]['port'], args.timeout, ping_queue)

    executor.shutdown(wait=True)
    logger.warning("All ping jobs have been completed, waiting for the database to catch up. (this will take a while)")

    ping_queue.put("STOP")
    db_thread.join()

    conn.commit()
    conn.close()
    logger.info("Parse complete!")

def main_update(max_workers, external):
    ping_queue = queue.Queue()

    conn = connect_to_db(read_config())
    init_db(conn)

    if not external:
        db_thread = threading.Thread(target=db_handler, args=(ping_queue, conn, True))
        db_thread.start()

    processed = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM main")
            db_length = cursor.fetchone()[0]
            for index in range(db_length):
                cursor.execute("SELECT ip_fk, port FROM main WHERE uid = ?", (index + 1,))
                request = cursor.fetchone()
                ip_fk = request[0]
                port = request[1]
                
                cursor.execute("SELECT address FROM ips WHERE uid = ?", (ip_fk,))
                ip = cursor.fetchone()[0]
                
                if (ip, port) not in processed:
                    executor.submit(ping_worker, ip, port, args.timeout, ping_queue)
                    processed.add((ip, port))

    if external:
        db_thread = threading.Thread(target=db_handler, args=(ping_queue, conn, True))
        db_thread.start()

    executor.shutdown(wait=True)
    logger.warning("All ping jobs have been completed, waiting for the database to catch up. (this will take a while)")

    ping_queue.put("STOP")
    db_thread.join()

    conn.commit()
    conn.close()
    logger.info("Update complete!")

def create_config():
    config = configparser.ConfigParser()
    config['database'] = {
        'username': 'root',
        'password': '',
        'host': 'localhost',
        'port': '3306',
        'database_name': 'novacolumn'
    }
    with open('novacolumn.conf', 'w') as file:
        file.write("; All this config file does is handle the database login.\n")
        file.write("; Note that the script WILL NOT create a database for you. You will need to do that yourself.\n")
        file.write("; If you plan to use this in a public database, make sure not to use root as the default user.\n")
        config.write(file)

def verify_usernames():
    conn = connect_to_db(read_config())
    init_db(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM playernames WHERE valid = 'waiting'")
    logger.debug("Requested usernames.")
    playernames = cursor.fetchall()
    validity = []
    for index in range(len(playernames)):
        check = mcuuid.MCUUID(uuid=str(playernames[index][2]).replace("-", ""))
        try:
            logger.debug(f"Checking {playernames[index][2]} for validity")
            usr = check.name
            logger.info(f"Valid UUID - [{usr}]")
            validity.append('true')
        except Exception:
            logger.info("Invalid UUID")
            validity.append('false')
    for index in range(len(validity)):
        logger.info(f"Updating database playernames - UID {playernames[index][0]} with {validity[index]}")
        cursor.execute("UPDATE playernames SET valid = ? WHERE uid = ?", (validity[index], playernames[index][0]))
    
    conn.commit()
    conn.close()
    logger.info("Username verification complete!")


if __name__ == "__main__":
    args = initialize_arguments()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Log everything at DEBUG level for file logging

    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_filename = datetime.now().strftime('novacolumn_%Y-%m-%d_%H-%M-%S.log')
    file_handler = logging.FileHandler(f'./logs/{log_filename}', 'w', 'utf8')
    file_handler.setLevel(logging.DEBUG)  # Log all levels to file
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    if args.verbose:
        console_handler.setLevel(logging.DEBUG)  # Show DEBUG in verbose mode
    else:
        console_handler.setLevel(logging.INFO)  # Otherwise, show only INFO and higher
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    if not os.path.exists('novacolumn.conf'):
        logger.critical(".conf file not found. Creating default conf...")
        create_config()
        logger.critical("Default .conf file created, please fill it out!")
        exit(1)
    else:
        logger.debug(".conf file found.")

    if args.update:
        logger.info('Updating entire database!')
        main_update(args.threads, args.external)
    elif args.verify:
        logger.info('Validating usernames:')
        verify_usernames()
    else:
        if not args.file:
            logger.critical('There was no .json file provided!')
            exit(1)
        try:
            with open(args.file, 'r', encoding='utf-8') as file:
                scan_data = json.load(file)
            scan_data[0]['ip']
        except KeyError:
            logger.critical('The .json file provided is not the correct format.')
            logger.critical('Are you sure this was generated by masscan?')
            exit(1)
        except FileNotFoundError:
            logger.critical('The .json file provided does not exist.')
            exit(1)
        main(scan_data, args.threads)