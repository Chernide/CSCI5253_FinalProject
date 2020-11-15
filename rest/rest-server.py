from flask import Flask, request, Response, jsonify
from google.cloud import storage
import jsonpickle, pickle
import platform
import io, os, sys
import pika, redis
import requests
import psycopg2

#######Database Variables#######
host = os.getenv('POSTGRES_HOST')
database = os.getenv('POSTGRES_DB')
user = os.getenv('POSTGRES_USER')
port = os.getenv('POSTGRES_PORT')
password = os.getenv('POSTGRES_PASSWORD')
################################

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '../Project_GCP_Credentials.json'
storage_client = storage.Client()


#init flask app
app = Flask(__name__)

logs_info_key = '{}.rest.info'.format(platform.node())
def log_info(message, channel, key=logs_info_key):
    channel.exchange_declare(exchange='logs', exchange_type='topic')
    channel.basic_publish(exchange='logs', routing_key=key, body = message) 

@app.route('/', methods=['GET'])
def heartbeat():
    return '<h1>Application Manager</h1><p>Use a valid endpoint</p>'

@app.route('/help', methods=['GET'])
def help_general():
    return '<h1>Application Manager Help<h1><p>This is an organizer application for college and jobs. It provides storage and query abilities for these applications. To get help on a specific type of applcation use: /help/college or /help/job</p>'

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
    json_in = request.data
    return None 

@app.route('/add/job', methods=['POST'])
def add_job_application():
    json_in = request.data
    return None 

@app.route('/query/college/<field>/<value>', methods=['GET'])
@app.route('/query/college/<field>/<value>/<inequality>', methods=['GET'])
def query_college(field, value, inequality='eq'):
    return None

@app.route('/query/job/<field>/<value>', methods=['GET'])
@app.route('/query/job/<field>/<value>/<inequality>', methods=['GET'])
def query_job(field, value, inequality='eq'):
    return None

@app.route('/update/college/<field>/<value>', methods=['PUT'])
def update_college(field, value):
    primaryKey = request.data
    return None

@app.route('/update/job/<field>/<value>', methods=['PUT'])
def update_job(field, value):
    primaryKey = request.data
    return None

@app.route('/delete/college', methods=['DELETE'])
def delete_college():
    primaryKey = request.data
    return None 

@app.route('/delete/job', methods=['DELETE'])
def delete_job():
    primaryKey = request.data
    return None 

app.run(host='0.0.0.0', port=5000)