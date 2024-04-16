# -*- coding: utf-8 -*-
import string
import time
import traceback
from typing import List

from confluent_kafka import Consumer, Producer

from utils.common import generate_random_string, get_env_conf
from utils.logger import logger


class KafkaClient:
    def __init__(
        self, kafka_conf_name: str = "kafka", servers_conf_name: str = "servers"
    ) -> None:
        """
        Initialize an instance of the KafkaClient class.

        Args:
            kafka_conf_name (str): The name of the kafka configuration. Defaults to "kafka".
            servers_conf_name (str): The name of the server configuration. Defaults to "servers".

        Returns:
            None
        """
        self._kafka_conf = get_env_conf(name=kafka_conf_name)
        self._servers_list = get_env_conf(name=servers_conf_name)
        self._topic = None
        self._group_id = None
        self._init()

    def _init(self) -> None:
        """
        Initialize the parameters and update kafka conf.

        Returns:
            None
        """
        self._topic = self._kafka_conf.pop("topic")
        logger.info(f"topic: {self._topic}")

        self._group_id = self._kafka_conf.pop("group.id")

        bootstrap_servers = ",".join(
            [f"""{i.get("ip")}:{i.get("port")}""" for i in self._servers_list]
        )
        self._kafka_conf.update({"bootstrap.servers": bootstrap_servers})
        logger.info(f"servers: {bootstrap_servers}")

    def _get_consumer_conf(self) -> dict:
        """
        Get the consumer configuration.

        Returns:
            dict: The consumer configuration.
        """
        consumer_conf = self._kafka_conf.copy()

        new_group = (
            self._group_id
            + "_"
            + generate_random_string(num=6, charset=string.ascii_lowercase)
        )
        consumer_conf.update({"group.id": new_group})
        logger.info(f"consumer group: {new_group}")

        consumer_conf.update({"auto.offset.reset": "earliest"})

        return consumer_conf

    def publish_kafka_message(self, message: str) -> None:
        """
        Publish a message to Kafka.

        Args:
            message (str): The message to be sent.

        Returns:
            None
        """
        producer = Producer(self._kafka_conf)
        producer.produce(self._topic, value=message.encode("utf-8"))
        producer.flush()

    def receive_historical_kafka_message(
        self, max_messages: int = 5, timeout: int = 10
    ) -> List[str]:
        """
        Receive historical Kafka messages from the specified topic and consumer group.

        Args:
            max_messages (int): The maximum number of messages to retrieve. Defaults to 5.
            timeout (int): The maximum time, in seconds, to wait for messages. Defaults to 10.

        Returns:
            List[str]: The list of historical Kafka messages.
        """
        consumer = Consumer(self._get_consumer_conf())
        consumer.subscribe([self._topic])

        logger.info(f"receiving historical kafka messages, timeout: {timeout}s")
        messages = []
        start_time = time.time()
        while time.time() - start_time < timeout:
            message = consumer.poll(1.0)

            if message is None:
                continue
            elif message.error():
                logger.error("error occurred:", message.error())
                break
            else:
                messages.append(message.value().decode("utf-8"))

        if len(messages) > max_messages:
            messages = messages[-max_messages:]

        consumer.close()
        logger.info(f"received {len(messages)} messages, kafka client closed")

        return messages

    def receive_realtime_kafka_message(self) -> None:
        """
        Receive realtime Kafka messages from the specified topic and consumer group.

        Returns:
            None
        """
        consumer = Consumer(self._get_consumer_conf())
        consumer.subscribe([self._topic])

        logger.info("receiving realtime kafka messages...")
        try:
            count = 1
            while True:
                message = consumer.poll(1.0)

                if message is None:
                    continue
                elif message.error():
                    logger.error("error occurred:", message.error())
                    raise KeyboardInterrupt
                else:
                    logger.info(
                        f"""received message [{str(count).center(5)}]: \n{message.value().decode("utf-8")}"""
                    )
                    count += 1
        except KeyboardInterrupt:
            consumer.close()
            logger.info("kafka client closed")


if __name__ == "__main__":
    try:
        KafkaClient().receive_realtime_kafka_message()
    except Exception as e:
        logger.error(f"{e}\n{traceback.format_exc()}")
