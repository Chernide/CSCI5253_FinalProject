from google.cloud import storage
import pickle
import platform
from PIL import Image
import io
import os
import sys
import pika

hostname = platform.node()
rabbitMQHost = os.getenv('RABBIT_SERVICE_HOST')

connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
channel = connection.channel()
channel.exchange_declare(exchange='toWorker', exchange_type='direct')
result = channel.queue_declare(queue='')
queue_name = result.method.queue
channel.queue_bind(exchange='toWorker', queue=queue_name, routing_key='toWorker')

infoKey = '{}.worker.info'.format(hostname)
def log_info(message, channel, key=infoKey):
    channel.exchange_declare(exchange='logs', exchange_type='topic')
    channel.basic_publish(exchange='logs', routing_key=key, body=message)

def insertApp(ch, method, properties, body):
    None

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=queue_name, on_message_callback=insertApp)
channel.start_consuming()