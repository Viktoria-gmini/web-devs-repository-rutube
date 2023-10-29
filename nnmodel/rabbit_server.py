import json
import os

import pika

from nnmodel.logger_utils import logger
from nnmodel.model_interface import NNModel
from nnmodel.rabbit_utils import Connector
from nnmodel.thread_utils import ThreadController

NN_INPUT_QUEUE_NAME = os.environ.get('NN_INPUT_QUEUE_NAME', 'nn-input')

connector = Connector.get_connector()
logger = logger.getChild('rabbit_nn_server')


class RabbitMQNNClient:
    def __init__(self):
        self.connection = connector.connect()
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=NN_INPUT_QUEUE_NAME)
        self.channel.basic_consume(queue=NN_INPUT_QUEUE_NAME, on_message_callback=self._on_request, auto_ack=False)
        self.model_interface = NNModel.get_model()

    def start(self):
        self.channel.start_consuming()

    def _on_request(self, ch, method: pika.spec.Basic.Deliver, props: pika.BasicProperties, body):
        logger.info(f"Received request: {body}")
        data = json.loads(body)
        print(data)
        try:
            nn_result = self.model_interface.predict(data['text'])
            result = {"words": [word.word for word in nn_result], "tags": [word.label for word in nn_result]}
        except Exception as e:
            logger.error(repr(e))
            result = {"error": f"Error: {repr(e)}"}
        result_str = str(json.dumps(result))
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id),
                         body=result_str)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"Sent answer: {result_str}")
        pass


def main():
    def run_server():
        rs = RabbitMQNNClient()
        rs.start()

    tc = ThreadController()
    tc.add_thread(run_server, name="Rabbit Server")
    tc.run_infinite(block=True)


if __name__ == '__main__':
    main()
