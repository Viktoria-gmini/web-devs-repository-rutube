import json
import threading
import time
import uuid
from typing import Callable, Iterable, Mapping

import pika
from pika.frame import Method

from thread_utils import ThreadController

NN_INPUT_QUEUE_NAME = 'nn-input'


class RabbitMQClient:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        callback_result: Method = self.channel.queue_declare(queue='', exclusive=True)
        self._callback_queue_name: str = callback_result.method.queue
        self.channel.basic_consume(
            queue=self._callback_queue_name,
            on_message_callback=self.on_response,
            auto_ack=True)

        self.response = None
        self.corr_id = None
        pass

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body
        pass

    def send_data(self, data: dict):
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key=NN_INPUT_QUEUE_NAME,
                                   properties=pika.BasicProperties(
                                       reply_to=self._callback_queue_name,
                                       correlation_id=self.corr_id,
                                   ),
                                   #  Message needs a string
                                   body=json.dumps(data))
        self.connection.process_data_events(time_limit=None)
        pass


class RabbitMQServer:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=NN_INPUT_QUEUE_NAME)
        self.channel.basic_consume(queue=NN_INPUT_QUEUE_NAME, on_message_callback=self.on_request, auto_ack=True)

    def start(self):
        self.channel.start_consuming()

    def on_request(self, ch, method: pika.spec.Basic.Deliver, props: pika.BasicProperties, body):
        data = json.loads(body)
        print(data)
        result = f"Hi there! Sent data has length as str: {len(body)}"
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id),
                         body=str(result))
        # ch.basic_ack(delivery_tag=method.delivery_tag)
        pass



def main():
    def run_server():
        rs = RabbitMQServer()
        rs.start()

    def run_client():
        rc = RabbitMQClient()
        while True:
            rc.send_data(data={"text": "hello!"})
            time.sleep(1)
    tc = ThreadController()
    tc.add_thread(run_server, name="Rabbit Server")
    tc.add_thread(run_client, name="Rabbit Client")
    tc.run_infinite(block=True)


if __name__ == '__main__':
    main()
