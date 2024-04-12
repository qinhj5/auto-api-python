# -*- coding: utf-8 -*-
import time
import string
from typing import List
from utils.logger import logger
from confluent_kafka import Consumer
from utils.common import get_env_conf, generate_random_string


class KafkaClient:
    def __init__(self,
                 consumer_conf_name: str = "kafka_consumer",
                 servers_conf_name: str = "forwarder_servers") -> None:
        """
        Initialize an instance of the KafkaClient class.

        Args:
            consumer_conf_name (str): The name of the consumer configuration. Defaults to "kafka_consumer".
            servers_conf_name (str): The name of the server configuration. Defaults to "forwarder_servers".

        Returns:
            None
        """
        self._consumer_conf = get_env_conf(name=consumer_conf_name)
        self._servers_list = get_env_conf(name=servers_conf_name)
        self._topic = None

    def _update_kafka_config(self) -> None:
        """
        Updates the Kafka configuration by generating a new consumer group ID and getting the topic name.

        Returns:
            None
        """
        group_id = self._consumer_conf.get("group.id")
        new_group_id = group_id + "_" + generate_random_string(num=6, charset=string.ascii_lowercase)
        self._consumer_conf.update({"group.id": new_group_id})
        logger.info(f"using group: {new_group_id}")
    
        self._topic = self._consumer_conf.pop("topic.name")
        logger.info(f"using topic: {self._topic}")

        self._consumer_conf.update({"bootstrap.servers": ",".join(self._servers_list)})
        logger.info(f"servers: {self._servers_list}")

        self._consumer_conf.update({"auto.offset.reset": "earliest"})

    def get_historical_kafka_message(self, max_messages: int = 5, timeout: int = 3) -> List[str]:
        """
        Get historical Kafka messages from the specified topic and consumer group.

        Args:
            max_messages (int): The maximum number of messages to retrieve. Defaults to 5.
            timeout (int): The maximum time, in seconds, to wait for messages. Defaults to 3.

        Returns:
            List[str]: The list of historical Kafka messages.
        """
        self._update_kafka_config()
        self._consumer_conf.update({"auto.offset.reset": "earliest"})
        consumer = Consumer(self._consumer_conf)
        consumer.subscribe([self._topic])

        logger.info("receiving historical kafka messages...")
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
        logger.info("kafka client closed")

        return messages

    def get_realtime_kafka_message(self) -> None:
        """
        Receive realtime Kafka messages from the specified topic and consumer group.

        Returns:
            None
        """
        self._update_kafka_config()
        consumer = Consumer(self._consumer_conf)
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
                    logger.info(f"""received message [{str(count).center(5)}]: \n{message.value().decode("utf-8")}""")
                    count += 1
        except KeyboardInterrupt:
            consumer.close()
            logger.info("kafka client closed")


if __name__ == "__main__":
    KafkaClient().get_realtime_kafka_message()
