from nnmodel.rabbit_server import RabbitMQNNClient
from nnmodel.thread_utils import ThreadController

def run_server():
    rabit_nn_server = RabbitMQNNClient()
    rabit_nn_server.start()


def main():
    thread_controller = ThreadController()
    thread_controller.add_thread(run_server, name="Rabbit NN Server")
    thread_controller.run_infinite()


if __name__ == '__main__':
    main()
