# -*- coding: utf-8 -*-
import traceback
from utils.logger import logger
from xmindparser import xmind_to_dict


class XmindParser:
    def __init__(self, xmind_file_path: str) -> None:
        """
        Initialize an instance of the XmindParser class.

        Args:
            xmind_file_path (str): The path to the XMind file.

        Returns:
            None
        """
        self._xmind_file_path = xmind_file_path

    def _count_leaf_nodes(self, node: dict) -> int:
        """
        Count the number of leaf nodes in a given node.

        Args:
            node (dict): The node to count the leaf nodes for.

        Returns:
            int: The number of leaf nodes in the given node.
        """
        if node.get("topics") is None:
            return 1
        else:
            count = 0
            for child in node["topics"]:
                count += self._count_leaf_nodes(child)
            return count

    def get_leaf_summary(self) -> None:
        """
        Get a summary of the leaf nodes in the XMind file.

        Returns:
            None
        """
        xmind_dict = xmind_to_dict(self._xmind_file_path)

        total_leaf_nodes_count = 0

        for sheet in xmind_dict:
            sheet_title = sheet["title"]
            root_topic = sheet["topic"]

            leaf_nodes_count = self._count_leaf_nodes(root_topic)
            logger.info(f"""Number of leaf nodes for "{sheet_title}": {leaf_nodes_count}""")

            total_leaf_nodes_count += leaf_nodes_count

        logger.info(f"Total number of leaf nodes across all canvases: {total_leaf_nodes_count}")


if __name__ == "__main__":
    try:
        # xmind_file_path is the path of your xmind file
        XmindParser(xmind_file_path="").get_leaf_summary()
    except Exception as e:
        logger.error(f"{e}\n{traceback.format_exc()}")
