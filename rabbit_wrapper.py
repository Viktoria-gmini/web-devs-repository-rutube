import json
import threading
import time
import uuid
from abc import ABC, abstractmethod

import pika
from pika.frame import Method

from thread_utils import ThreadController

NN_INPUT_QUEUE_NAME = 'nn-input'
MAX_NN_WAITING_TIME_SECONDS = 30


class NNInterface(ABC):

    @abstractmethod
    def post(self, data: dict) -> dict:
        raise NotImplementedError

    @staticmethod
    def make_rabbitmq() -> 'NNInterface':
        return RabbitMQClient()


class NNException(Exception):
    pass


class NNFailTimeoutException(NNException):
    pass


class NNReturnedBadJSONException(NNException):
    pass


class RabbitMQClient(NNInterface):
    def post(self, data: dict) -> dict:
        self._send_data(data)
        if not self._result_event.wait(MAX_NN_WAITING_TIME_SECONDS):
            raise NNFailTimeoutException(f"NN failed to respond in {MAX_NN_WAITING_TIME_SECONDS} seconds")
        self._result_event.clear()
        return self.response

    def __init__(self):
        self._result_event = threading.Event()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
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

    def _on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            try:
                response_str = bytes.decode(body, encoding='utf-8')
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
                                   body=json.dumps(data))
        self.connection.process_data_events(time_limit=None)
        pass


class RabbitMQServer:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=NN_INPUT_QUEUE_NAME)
        self.channel.basic_consume(queue=NN_INPUT_QUEUE_NAME, on_message_callback=self._on_request, auto_ack=False)

    def start(self):
        self.channel.start_consuming()

    @staticmethod
    def _on_request(ch, method: pika.spec.Basic.Deliver, props: pika.BasicProperties, body):
        data = json.loads(body)
        print(data)
        result = {"result": f"Hi there! Sent data has length as str: {len(body)}"}
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id),
                         body=str(json.dumps(result)))
        ch.basic_ack(delivery_tag=method.delivery_tag)
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
            pass

    tc = ThreadController()
    tc.add_thread(run_server, name="Rabbit Server")
    # tc.add_thread(run_client, name="Rabbit Client")
    tc.run_infinite(block=True)


if __name__ == '__main__':
    main()
