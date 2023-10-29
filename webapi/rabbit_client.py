import json
import os
import threading
import time
import uuid

import pika
from pika.frame import Method

from webapi.nn_interface import NNInterface, NNFailTimeoutException, NNReturnedBadJSONException
from webapi.rabbit_empty_server import RabbitMQEmptyServer
from webapi.thread_utils import ThreadController
from webapi.rabbit_utils import Connector

NN_INPUT_QUEUE_NAME = os.environ.get('NN_INPUT_QUEUE_NAME', 'nn-input')
MAX_NN_WAITING_TIME_SECONDS = os.environ.get('MAX_NN_WAITING_TIME_SECONDS', 30)
BASE_ENCODING = os.environ.get("BASE_ENCODING", "utf-8")

connector = Connector.get_connector()


class RabbitMQClient(NNInterface):
    def post(self, data: dict) -> dict:
        self._send_data(data)
        if not self._result_event.wait(MAX_NN_WAITING_TIME_SECONDS):
            raise NNFailTimeoutException(f"NN failed to respond in {MAX_NN_WAITING_TIME_SECONDS} seconds")
        self._result_event.clear()
        return self.response

    def __init__(self):
        self._result_event = threading.Event()
        self.connection = connector.connect()
        self.channel = self.connection.channel()
        callback_result: Method = self.channel.queue_declare(queue='', exclusive=True)
        self._callback_queue_name: str = callback_result.method.queue
        self.channel.basic_consume(
            queue=self._callback_queue_name,
            on_message_callback=self._on_response,
            auto_ack=True)

        self.response = None
        self.corr_id = None
        pass

    def _on_response(self, _, __, props, body):
        if self.corr_id == props.correlation_id:
            try:
                response_str = bytes.decode(body, encoding=BASE_ENCODING)
                self.response = dict(json.loads(response_str))
                self._result_event.set()
            except Exception as e:
                print(e)
                raise NNReturnedBadJSONException(f"NN returned bad data: {body}")
        pass

    def _send_data(self, data: dict):
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key=NN_INPUT_QUEUE_NAME,
                                   properties=pika.BasicProperties(
                                       reply_to=self._callback_queue_name,
                                       correlation_id=self.corr_id,
                                   ),
                                   #  Message needs a string
                                   body=json.dumps(data).encode())
        self.connection.process_data_events(time_limit=MAX_NN_WAITING_TIME_SECONDS)
        pass


def make_rabbitmq() -> 'NNInterface':
    return RabbitMQClient()


def main():
    def run_server():
        rs = RabbitMQEmptyServer()
        rs.start()

    def run_client():
        rc = RabbitMQClient()
        while True:
            rc.post(data={"text": "hello!"})
            time.sleep(1)
            pass

    tc = ThreadController()
    tc.add_thread(run_server, name="Rabbit Server")
    # tc.add_thread(run_client, name="Rabbit Client")
    tc.run_infinite(block=True)


if __name__ == '__main__':
    main()
