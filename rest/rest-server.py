from flask import Flask, request, Response, jsonify
from google.cloud import storage
import jsonpickle, pickle
import platform
import io, os, sys
import pika, redis
import requests
import psycopg2
import json

#######Database Variables#######
host = os.getenv('POSTGRES_HOST')
database = os.getenv('POSTGRES_DB')
user = os.getenv('POSTGRES_USER')
port = os.getenv('POSTGRES_PORT')
password = os.getenv('POSTGRES_PASSWORD')
################################
rabbitMQHost = os.getenv("RABBITMQ_SERVICE_HOST")
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '../Project_GCP_Credentials.json'
storage_client = storage.Client()
bucket = storage_client.bucket('finalproj-5253')

#init flask app
app = Flask(__name__)

acceptable_college_app_fields = ['Personal Info', 'First_Name', 'Last_Name', 'Email', 'Address', 'DOB', 'Education', 'School', 'GPA', 'Extracurriculars', 'Awards', 'Test Scores', 'SAT', 'ACT', 'College', 'Major', 'Essay', 'Picture']
acceptable_job_app_fields = ['Personal Info', 'First_Name', 'Last_Name', 'Email', 'Address', 'DOB', 'Highest Achieved Education', 'Institution', 'Major', 'GPA', 'Work Experience (3 MAX)', 'Job 1', 'Job 2', 'Job 3', 'Company', 'Title', 'Duties', 'Length of Employment', 'Current Job', 'Job Info', 'Company', 'Position', 'Required Pay', 'Picture']

logs_info_key = '{}.rest.info'.format(platform.node())
def log_info(message, channel, key=logs_info_key):
    channel.exchange_declare(exchange='logs', exchange_type='topic')
    channel.basic_publish(exchange='logs', routing_key=key, body = message) 

@app.route('/', methods=['GET'])
def heartbeat():
    return '<h1>Application Manager</h1><p>Use a valid endpoint</p>'

@app.route('/help', methods=['GET'])
def help_general():
    return '<h1>Application Manager Help<h1><p>This is an organizer application for college and jobs. It provides storage and query abilities for these applications. To get help on a specific type of applcation use: /help/college or /help/job. Pictures are encouraged but not required. And remember only upload one picture of yourself. It will be applied to all applications with the same name.</p>'

@app.route('/help/college', methods=['GET'])
def help_college():
    sample_college_app = {
        'Personal Info': {
            'First_Name': 'John',
            'Last_Name': 'Smith',
            'Email': 'john.smith@email.com',
            'Address': '123 Main St.',
            'DOB': '04/12/1998'
        },
        'Education': {
            'School': 'John Smiths\' High School',
            'GPA': 3.5,
            'Extracurriculars': ['Basketball', 'Debate'],
            'Awards': ['National Honors Society'],
            'Test Scores': {
                'SAT': 2000,
                'ACT': 32
            }
        },
        'College': {
            'School': 'University of Colorado At Boulder',
            'Major': 'Computer Science Engineering',
            'Essay': 'This is a sample college essay'
        }, 
        'Picture': 'https://storage.googleapis.com/cu-csci-5253/lfw/Daniel_Radcliffe/Daniel_Radcliffe_0001.jpg'
    }
    return jsonify({'Sample College Application': sample_college_app})

@app.route('/help/job', methods=['GET'])
def help_job():
    sample_job_app = {
        'Personal Info': {
            'First_Name': 'John',
            'Last_Name': 'Smith',
            'Email': 'john.smith@email.com',
            'Address': '123 Main St.',
            'DOB': '04/12/1998'
        }, 
        'Highest Achieved Education': {
            'Institution': 'University of Colorado At Boulder',
            'Major': 'Computer Science Engineering',
            'GPA': 3.86
        },
        'Work Experience (3 MAX)': {
            'Job 1': {
                'Company': 'Noodles & Company', 
                'Title': 'Shift Manager',
                'Duties': ['Create Schedule', 'Oversee employees'],
                'Length of Employment': '1 year 6 months',
                'Current Job': True
            },
            'Job 2': {
                'Company': 'Ball Aerospace', 
                'Title': 'Software Engineer Intern',
                'Duties': ['Utilized areospace software'],
                'Length of Employment': '3 months',
                'Current Job': False
            }
        },
        'Job Info': {
            'Company': 'United Launch Alliance',
            'Position': 'Embedded Software Engineer',
            'Required Pay': 65000
        }
    }

    return jsonify({'Sample Job Application': sample_job_app})

@app.route('/add/college', methods=['POST'])
def add_college_application():
    application = request.get_json()
    if application is not None:
        is_valid = True
        for k in application.keys():
            if k in acceptable_college_app_fields and k != 'Picture':
                for k2 in application[k].keys():
                    if k2 == 'Test Scores':
                        for k3 in application[k][k2].keys():
                            if k3 not in acceptable_college_app_fields:
                                is_valid = False
                                break
                    elif k2 not in acceptable_college_app_fields:
                        is_valid = False
                        break
            elif k != 'Picture':
                is_valid = False
                break
        if is_valid:
            connection = psycopg2.connect(user = user, password = password, host = host, port = port, database = database)
            cursor = connection.cursor()
            dupe_query = """ SELECT COUNT(*) FROM College WHERE first_name = %s and last_name = %s and school = %s"""
            dupe_query_params = (application['Personal Info']['First_Name'], application['Personal Info']['Last_Name'], application['College']['School'])
            cursor.execute(dupe_query, dupe_query_params)
            count = cursor.fetchall()
            if(count[0][0] == 1):
                return jsonify({'Application validity:': is_valid, 'Duplicate': 'Yes', 'Unique Key': [application['Personal Info']['First_Name'], application['Personal Info']['Last_Name'], application['College']['School']]})
            cursor.close()
            connection.close()

            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
            channel = connection.channel()
            log_info("JSON was valid", channel)
            channel.exchange_declare(exchange='toWorker', exchange_type='direct')
            message = {"College": application}
            msg_body = pickle.dumps(message)
            channel.basic_publish(exchange='toWorker', routing_key='toWorker', body=msg_body)
            if 'Picture' in application.keys():
                log_info("Picture provided", channel)
                pic_bytes = requests.get(application['Picture']).content
                key = application['Personal Info']['First_Name'] + '_' + application['Personal Info']['Last_Name']
                bucket.blob(key).upload_from_string(pic_bytes)
            connection.close()
        return jsonify({'Application validity:': is_valid, 'Unique Key': [application['Personal Info']['First_Name'], application['Personal Info']['Last_Name'], application['College']['School']]})
    else:
        return jsonify({'Error': 'Not in JSON format'})

@app.route('/add/job', methods=['POST'])
def add_job_application():
    application = request.get_json()
    if application is not None:
        is_valid = True
        for k in application.keys():
            if k in acceptable_job_app_fields:
                for k2 in application[k].keys():
                    if k2 in acceptable_job_app_fields:
                        if k2 == 'Job 1' or k2 == 'Job 2' or k2 == 'Job 3':
                            for k3 in application[k][k2].keys():
                                if k3 not in acceptable_job_app_fields:
                                    is_valid = False
                                    break
                    else:
                        is_valid = False
                        break
            else:
                is_valid = False
                break
        if is_valid:
            connection = psycopg2.connect(user = user, password = password, host = host, port = port, database = database)
            cursor = connection.cursor()
            dupe_query = """ SELECT COUNT(*) FROM Job WHERE first_name = %s and last_name = %s and company = %s"""
            dupe_query_params = (application['Personal Info']['First_Name'], application['Personal Info']['Last_Name'], application['Job Info']['Company'])
            cursor.execute(dupe_query, dupe_query_params)
            count = cursor.fetchall()
            if(count[0][0] == 1):
                return jsonify({'Application validity:': is_valid, 'Duplicate': "Yes", 'Unique Key': [application['Personal Info']['First_Name'], application['Personal Info']['Last_Name'], application['Job Info']['Company']]})
            cursor.close()
            connection.close()

            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
            channel = connection.channel()
            log_info("JSON was valid", channel)
            channel.exchange_declare(exchange='toWorker', exchange_type='direct')
            message = {"Job": application}
            msg_body = pickle.dumps(message)
            channel.basic_publish(exchange='toWorker', routing_key='toWorker', body=msg_body)
            if 'Picture' in application.keys():
                log_info("Picture provided", channel)
                pic_bytes = requests.get(application['Picture']).content
                key = application['Personal Info']['First_Name'] + '_' + application['Personal Info']['Last_Name']
                bucket.blob(key).upload_from_string(pic_bytes)
            connection.close()
        return jsonify({'Application validity:': is_valid, 'Unique Key': [application['Personal Info']['First_Name'], application['Personal Info']['Last_Name'], application['Job Info']['Company']]})
    else:
        return jsonify({'Error': 'Not in JSON format'})

@app.route('/query/college/<field>/<value>', methods=['GET'])
@app.route('/query/college/<field>/<value>/<inequality>', methods=['GET'])
def query_college(field, value, inequality='eq'):
    equality = '='
    if(inequality == 'lt'):
        equality = '<'
    elif(inequality == 'leq'):
        equality = '<='
    elif(inequality == 'ne'):
        equality = '!='
    elif(inequality == 'gt'):
        equality = '>'
    elif(inequality == 'geq'):
        equality = '>='
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
    channel = connection.channel()
    connection2 = psycopg2.connect(user = user, password = password, host = host, port = port, database = database)
    cursor = connection2.cursor()
    try:
        query_sql = """SELECT * FROM College where {} {} {}""".format(field, equality, value)
        log_info("QUERY: {}".format(query_sql), channel)
        cursor.execute(query_sql)
        rows = cursor.fetchall()
        apps = []
        for r in rows:
            row = []
            for element in r:
                row.append(str(element))
            apps.append(row)
        connection2.commit()
    except Exception as e:
        return jsonify({"Error": "Something went wrong with your query. Here is the error: " + str(e)})
    finally:
        connection.close()
        cursor.close()
        connection2.close()
    return jsonify({'Return applications': apps})

@app.route('/query/job/<field>/<value>', methods=['GET'])
@app.route('/query/job/<field>/<value>/<inequality>', methods=['GET'])
def query_job(field, value, inequality='eq'):
    equality = '='
    if(inequality == 'lt'):
        equality = '<'
    elif(inequality == 'leq'):
        equality = '<='
    elif(inequality == 'ne'):
        equality = '!='
    elif(inequality == 'gt'):
        equality = '>'
    elif(inequality == 'geq'):
        equality = '>='
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
    channel = connection.channel()
    connection2 = psycopg2.connect(user = user, password = password, host = host, port = port, database = database)
    cursor = connection2.cursor()
    try:
        query_sql = """SELECT * FROM Job where {} {} {}""".format(field, equality, value)
        log_info("QUERY: {}".format(query_sql), channel)
        cursor.execute(query_sql)
        rows = cursor.fetchall()
        apps = []
        for r in rows:
            row = []
            for element in r:
                row.append(str(element))
            apps.append(row)
        connection2.commit()
    except Exception as e:
        return jsonify({"Error": "Something went wrong with your query. Here is the error: " + str(e)})
    finally:
        connection.close()
        cursor.close()
        connection2.close()
    return jsonify({'Return applications': apps})

@app.route('/update/college/<field>/<value>', methods=['PUT'])
def update_college(field, value):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
    channel = connection.channel()
    connection2 = psycopg2.connect(user = user, password = password, host = host, port = port, database = database)
    cursor = connection2.cursor()
    primaryKey = request.get_json()
    fname = primaryKey["First Name"]
    lname = primaryKey["Last Name"]
    school = primaryKey["School"]
    update_sql = """UPDATE College SET {} = %s where first_name = %s and last_name = %s and school = %s""".format(field)
    try:
        update_params = (value, fname, lname, school)
        cursor.execute(update_sql, update_params)
        updated_rows = cursor.rowcount
        if(updated_rows != 1):
            raise Exception("Attempting to update more than 1 row")
        else:
            connection2.commit()
    except (Exception, psycopg2.errors.UndefinedColumn) as e:
        return jsonify({"ERROR WHILE UPDATING": str(e)})
    finally:
        connection.close()
        cursor.close()
        connection2.close()
    return jsonify({"Application Update": "Successfull"})

@app.route('/update/job/<field>/<value>', methods=['PUT'])
def update_job(field, value):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
    channel = connection.channel()
    connection2 = psycopg2.connect(user = user, password = password, host = host, port = port, database = database)
    cursor = connection2.cursor()
    primaryKey = request.get_json()
    fname = primaryKey["First Name"]
    lname = primaryKey["Last Name"]
    company = primaryKey["Company"]
    update_sql = """UPDATE Job SET {} = %s where first_name = %s and last_name = %s and company = %s""".format(field)
    try:
        update_params = (value, fname, lname, company)
        cursor.execute(update_sql, update_params)
        updated_rows = cursor.rowcount
        if(updated_rows != 1):
            raise Exception("Attempting to update more than 1 row")
        else:
            connection2.commit()
    except (Exception, psycopg2.errors.UndefinedColumn) as e:
        return jsonify({"ERROR WHILE UPDATING": str(e)})
    finally:
        connection.close()
        cursor.close()
        connection2.close()
    return jsonify({"Application Update": "Successfull"})

@app.route('/delete/college', methods=['DELETE'])
def delete_college():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
    channel = connection.channel()
    connection2 = psycopg2.connect(user = user, password = password, host = host, port = port, database = database)
    cursor = connection2.cursor()
    primaryKey = request.get_json()
    fname = primaryKey["First Name"]
    lname = primaryKey["Last Name"]
    school = primaryKey["School"]
    delete_query = """DELETE FROM College WHERE first_name = %s and last_name = %s and school = %s RETURNING *"""
    delete_query_params = (fname, lname, school)
    log_info("Attempting to delete: {}".format(delete_query_params), channel)
    return_statement = None
    cursor.execute(delete_query, delete_query_params)
    row_returned = cursor.fetchone()
    if(row_returned == None):
        return_statement = jsonify({"Failed": "Delete action has failed. Make sure primary key is correct."})
    else:
        connection2.commit()
        return_statement = jsonify({"Success": "Delete has successfully completed."})
    cursor.close()
    connection2.close()
    connection.close()
    return return_statement

@app.route('/delete/job', methods=['DELETE'])
def delete_job():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
    channel = connection.channel()
    connection2 = psycopg2.connect(user = user, password = password, host = host, port = port, database = database)
    cursor = connection2.cursor()
    primaryKey = request.get_json()
    fname = primaryKey["First Name"]
    lname = primaryKey["Last Name"]
    company = primaryKey["Company"]
    delete_query = """DELETE FROM Job WHERE first_name = %s and last_name = %s and company = %s RETURNING *"""
    delete_query_params = (fname, lname, company)
    log_info("Attempting to delete: {}".format(delete_query_params), channel)
    return_statement = None
    cursor.execute(delete_query, delete_query_params)
    row_returned = cursor.fetchone()
    if(row_returned == None):
        return_statement = jsonify({"Failed": "Delete action has failed. Make sure primary key is correct."})
    else:
        connection2.commit()
        return_statement = jsonify({"Success": "Delete has successfully completed."})
    cursor.close()
    connection2.close()
    connection.close()
    return return_statement

app.run(host='0.0.0.0', port=5000)