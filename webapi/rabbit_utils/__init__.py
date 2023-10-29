import os
import time
from typing import Any

import pika
from pika import BlockingConnection
from pika.connection import Connection

from webapi.logger_utils import logger

logger = logger.getChild("rabbit_utils")


def create_queue(channel, queue_name):
    channel.queue_declare(
        queue=queue_name,
        durable=True,
        exclusive=False,  # если очередь уже существует,
        auto_delete=False,
        arguments={'x-max-priority': 255, 'x-queue-type=classic': 'classic'}
    )
    logger.info(f'Queue {queue_name} has been added')


class ConnectionInfo:
    def __init__(self, connection: BlockingConnection):
        self.connection = connection


class Connector:
    _connector: 'Connector' = None

    def __init__(self) -> None:
        self.port = None
        self._connection: Connection | None = None
        self.virtual_host = None
        self.output_queue = None
        self.input_queue = None
        self.username = None
        self.password = None
        self.ip = None
        self.url = None
        self.load_env_from_os()

    def load_env_from_os(self):
        self.url = os.environ.get('RABBIT_URL', 'localhost')
        # protocol = self.url.split('//')[0].rstrip(':')
        without_protocol = self.url.split('//')[-1]
        if '@' in self.url:
            before_host = without_protocol.split('@')[0]
            self.username = before_host.split(':')[0]
            if len(before_host.split(':')) > 1:
                self.password = before_host.split(':')[1]
        after_username = without_protocol.split('@')[-1]
        host_with_port = after_username.split('/')[0]
        self.ip = host_with_port.split(':')[0]
        if len(host_with_port.split(':')) > 1:
            self.port = host_with_port.split(':')[1]
        self.virtual_host = ''
        if len(after_username.split('/')) > 1:
            self.virtual_host = after_username.split('/')[1]

        if len(self.virtual_host) == 0:
            self.virtual_host = '/'

        logger.info('Envs are loaded')

    def __enter__(self) -> ConnectionInfo:
        """
        :return: connection, channel, input_queue, output_queue
        """
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._connection.is_open:
            self._connection.close()

    def connect(self) -> Any:
        ip = self.ip
        port = self.port if self.port is not None else pika.ConnectionParameters.DEFAULT_PORT
        virtual_host = self.virtual_host
        username = self.username if self.username is not None else pika.ConnectionParameters.DEFAULT_USERNAME
        password = self.password if self.password is not None else pika.ConnectionParameters.DEFAULT_PASSWORD
        tries = 0
        while tries < 5:
            try:
                tries += 1
                logger.info(f'Trying to connect #{tries} time')
                connection = pika.BlockingConnection(
                    [
                        pika.ConnectionParameters(
                            host=ip,
                            port=port,
                            virtual_host=virtual_host,
                            credentials=pika.PlainCredentials(
                                username=username,
                                password=password,
                            ),
                        )
                    ],

                )
                self._connection = connection
                # channel = connection.channel()
                logger.info('Connection successful')

                # create_queue(channel, self.input_queue)
                # create_queue(channel, self.output_queue)

                return self._connection
            except Exception as _:
                logger.info(f'Connection failed. Waiting for a 5 seconds...')
                time.sleep(5)

    @classmethod
    def get_connector(cls):
        if cls._connector is None:
            cls._connector = cls()
        return cls._connector
