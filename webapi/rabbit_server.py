import json
import os

import pika

from webapi.rabbit_utils import Connector
from webapi.thread_utils import ThreadController

NN_INPUT_QUEUE_NAME = os.environ.get('NN_INPUT_QUEUE_NAME', 'nn-input')

connector = Connector.get_connector()


class RabbitMQEmptyServer:
    def __init__(self):
        self.connection = connector.connect()
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
        rs = RabbitMQEmptyServer()
        rs.start()

    tc = ThreadController()
    tc.add_thread(run_server, name="Rabbit Server")
    tc.run_infinite(block=True)


if __name__ == '__main__':
    main()
