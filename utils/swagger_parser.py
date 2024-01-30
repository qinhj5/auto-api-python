# -*- coding: utf-8 -*-
import os
import re
import sys
import json
import black
import shutil
import keyword
import requests
import builtins
from config.conf import Global
from utils.logger import logger
from utils.dirs import utils_dir
from typing import Tuple, Generator


class SwaggerParser:
    def __init__(self, swagger_url: str) -> None:
        """
        Initialize the class.

        Args:
            swagger_url (str): The URL of the Swagger file.

        Returns:
            None
        """
        self._swagger_url = swagger_url

    @staticmethod
    def _get_python_type(java_type: str) -> str:
        """
        Get the Python type based on the Java type.

        Args:
            java_type (str): Java type.

        Returns:
            str: Python type.
        """
        python_type_mapping = {
            "string": "str",
            "integer": "int",
            "boolean": "bool"
        }
        return python_type_mapping.get(java_type, "Any")

    @staticmethod
    def _clear_tmp_dir() -> None:
        """
        Clears the temporary directory.

        Returns:
            None
        """
        tmp_dir = os.path.abspath(os.path.join(utils_dir, "../tmp"))
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

    @staticmethod
    def _create_package_dir(name: str) -> None:
        """
        Creates package directories for API and testcases.

        Args:
            name (str): The name of the package.

        Returns:
            None
        """
        api_dir = os.path.abspath(os.path.join(utils_dir, f"../tmp/api/{name}"))
        os.makedirs(api_dir, exist_ok=True)
        init_path = os.path.abspath(os.path.join(api_dir, f"__init__.py"))
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("# -*- coding: utf-8 -*-\n")

        testcases_dir = os.path.abspath(os.path.join(utils_dir, f"../tmp/testcases/{name}"))
        os.makedirs(testcases_dir, exist_ok=True)
        init_path = os.path.abspath(os.path.join(testcases_dir, f"__init__.py"))
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("# -*- coding: utf-8 -*-\n")

        init_path = os.path.abspath(os.path.join(utils_dir, f"../tmp/__init__.py"))
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("# -*- coding: utf-8 -*-\n")

    @staticmethod
    def _remove_non_alphabet_from_start(string: str) -> str:
        """
        Remove all non-alphabetic characters from the start of a string until the first alphabet character.

        Args:
            string (str): The input string.

        Returns:
            str: The modified string with non-alphabetic characters removed from the start.
        """
        pattern = r"^[^a-zA-Z]+"
        result = re.sub(pattern, "", string)
        return result

    @staticmethod
    def _pascal_to_snake(name: str) -> str:
        """
        Converts pascal_case to snake_case.

        Args:
            name (str): The input pascal_case string.

        Returns:
            str: The converted snake_case string.
        """
        name = SwaggerParser._remove_non_alphabet_from_start(name.strip())
        words = re.findall(r"[A-Z]+[a-z\d]*|[A-Z]?[a-z\d]*", name)
        new_words = [word.lower() for word in words if word != ""]

        result = []

        for i, word in enumerate(new_words):
            if i > 0 and word.isdigit():
                result[-1] += word
            else:
                result.append(word)

        return "_".join(result)

    @staticmethod
    def _snake_to_pascal(snake_name: str) -> str:
        """
        Converts snake_case to PascalCase.

        Args:
            snake_name (str): The input snake_case string.

        Returns:
            str: The converted PascalCase string.
        """
        words = snake_name.split("_")
        pascal_name = "".join(word.capitalize() for word in words)
        return pascal_name

    def _get_swagger_json(self) -> Generator[tuple, None, None]:
        """
        Get Swagger JSON data by making a request to the specified Swagger URL.

        Yields:
            tuple: A tuple containing the API URI and its details.

        Raises:
            ValueError: If the Swagger URL response is not a valid JSON.
        """
        response = requests.get(self._swagger_url, headers=Global.constants.HEADERS)

        if response.status_code == 200:
            try:
                response.json()
            except ValueError:
                logger.error(f"Please check Swagger URL response: {response.text}")
            else:
                for api, api_details in response.json().get("paths", dict()).items():
                    yield api, api_details
        else:
            logger.error("Failed to request Swagger URL")
            sys.exit(1)

    def _get_swagger_dict(self) -> dict:
        """
        Get a dictionary representation of Swagger data.

        Returns:
            dict: A dictionary representing Swagger data.
        """
        json_generator = self._get_swagger_json()
        swagger_dict = {}
        for uri, api_details in json_generator:
            for api_method, api_detail in api_details.items():
                module_name = SwaggerParser._pascal_to_snake(api_detail["tags"][0])
                SwaggerParser._create_package_dir(module_name)
                api = {"uri": uri, "method": api_method, "detail": api_detail}
                if module_name in swagger_dict.keys():
                    swagger_dict[module_name].append(api)
                else:
                    swagger_dict[module_name] = []
                    swagger_dict[module_name].append(api)

        return swagger_dict

    @staticmethod
    def _convert_path_params(path: str) -> str:
        """
        Convert Swagger path parameters to snake_case.

        Args:
            path (str): The Swagger API path.

        Returns:
            str: The converted path with parameters in snake_case.
        """
        matches = re.findall(r"{(.*?)}", path)
        for match in matches:
            path = path.replace(match, SwaggerParser._avoid_keywords(SwaggerParser._pascal_to_snake(match)))
        return path

    @staticmethod
    def _get_deduplicated_params(params: list) -> list:
        """
        Deduplicate parameters by removing duplicates based on snake_case names.

        Args:
            params (list): List of Swagger API parameters.

        Returns:
            list: Deduplicated list of Swagger API parameters.
        """
        params.reverse()
        deduplicated_params = []
        snake_names = []
        for param in params:
            if param.get("name") is None:
                continue
            if param.get("required") is None:
                param.update({"required": False})
            snake_name = SwaggerParser._pascal_to_snake(param["name"])
            if snake_name not in snake_names:
                deduplicated_params.append(param)
                snake_names.append(snake_name)

        return deduplicated_params

    @staticmethod
    def _get_wrapped_string(long_string: str, length: int = 110, indent: int = 8, replace_colon: bool = False) -> str:
        """
        Generate wrapped string by splitting a long string into smaller segments.

        Args:
            long_string (str): The long string to be split.
            length (int): The maximum length of each segment. Defaults to 110.
            indent (int): The number of spaces to indent each segment. Defaults to 8.
            replace_colon (bool): Whether to replace colons in the string. Defaults to False.

        Returns:
            str: The wrapped string with each segment smaller than the specified length.
        """
        if replace_colon:
            long_string = long_string.replace(":", " - ")
        words = long_string.split()
        wrapped_strings = []

        current_segment = ""
        for word in words:
            if len(current_segment + word) <= length:
                current_segment += word + " "
            else:
                wrapped_strings.append(current_segment.strip())
                current_segment = word + " "

        if current_segment:
            wrapped_strings.append(current_segment.strip())

        return f"""\n{" " * indent}""".join(wrapped_strings)

    @staticmethod
    def _avoid_keywords(name: str) -> str:
        """
        Avoid using Python keywords or built-in names as name.

        Args:
            name (str): The name to be checked.

        Returns:
            str: The modified name.

        """
        if keyword.iskeyword(name) or name in dir(builtins):
            name = f"param_{name}"
        return name

    @staticmethod
    def _get_api_func(api: dict) -> Tuple[str, bool]:
        """
        Generate API function code based on Swagger API details.

        Args:
            api (dict): Swagger API details.

        Returns:
            Tuple[str, bool]: The generated function code and a boolean indicating whether List is used in the function.
        """
        method = api["method"]
        snake_name = SwaggerParser._pascal_to_snake(api["detail"]["operationId"])
        if snake_name.startswith(method):
            func_name = snake_name
        else:
            func_name = f"""{method}_{SwaggerParser._pascal_to_snake(api["detail"]["operationId"])}"""

        logger.info(json.dumps(api["detail"]))

        summary = api["detail"].get("summary", "Null")

        summary = SwaggerParser._get_wrapped_string(summary)

        uri = SwaggerParser._convert_path_params(api["uri"])

        params = api["detail"].get("parameters", [])
        if params:
            params = SwaggerParser._get_deduplicated_params(params)
            params = sorted(params, key=lambda x: x["required"], reverse=True)

        params_list = []
        params_dict = {}
        header_dict = {}
        data_dict = {}
        json_dict = {}
        use_list = False
        for param in params:
            param_name = SwaggerParser._pascal_to_snake(param["name"])
            param_name = SwaggerParser._avoid_keywords(param_name)
            param_type = SwaggerParser._get_python_type(param.get("type"))

            if param.get("type") == "array":
                list_inner_type = SwaggerParser._get_python_type(param["items"]["type"])
                param_type = f"List[{list_inner_type}]"
                use_list = True

            param_desc = param.get("description", "null")
            param_item = ({param_name: {"type": param_type, "desc": param_desc}}
                          if param["required"]
                          else {param_name: {"type": f"{param_type} = None", "desc": param_desc}})
            params_list.append(param_item)

            if param.get("in", "body") == "query":
                params_dict.update({param["name"]: param_name})
            elif param.get("in", "body") == "header":
                header_dict.update({param["name"]: param_name})
            elif param.get("in", "body") == "formData":
                data_dict.update({param["name"]: param_name})
            elif param.get("in", "body") == "body":
                json_dict.update({param["name"]: param_name})

        params_header = ""
        if params_list:
            params_header = (", " +
                             ", ".join(
                                 [f"""{next(iter(item.keys()))}: {item[next(iter(item.keys()))]["type"]}"""
                                  for item in params_list]))
        func_header = f"""\n    def {func_name}(self{params_header}) -> Dict[str, Any]:\n"""

        func_body = "        \"\"\"\n        %s\n\n" % summary
        func_body += "        Args:\n            self\n"
        for item in params_list:
            func_body += (f"""            {next(iter(item.keys()))} ({item[next(iter(item.keys()))]["type"]}): """ +
                          f"""{SwaggerParser._get_wrapped_string(item[next(iter(item.keys()))]["desc"],
                                                                 length=70, indent=12, replace_colon=True)}\n""")
        func_body += "\n        Returns:\n            Dict[str, Any]: " \
                     "The response content of the request as a dictionary.\
                      \n        \"\"\"\n"

        request_list = []
        if params_dict:
            partial_str = ", ".join([f""""{k}": {v}""" for k, v in params_dict.items()])
            func_body += """        params_dict = {%s}\n""" % partial_str
            request_list.append("params=params_dict")
        if header_dict:
            partial_str = ", ".join([f""""{k}": {v}""" for k, v in header_dict.items()])
            func_body += """        headers_dict = {%s}\n""" % partial_str
            request_list.append("headers=headers_dict")
        if data_dict:
            partial_str = ", ".join([f""""{k}": {v}""" for k, v in data_dict.items()])
            func_body += """        data_dict = {%s}\n""" % partial_str
            request_list.append("data=data_dict")
        if json_dict:
            partial_str = ", ".join([f""""{k}": {v}""" for k, v in json_dict.items()])
            func_body += """        json_dict = {%s}\n""" % partial_str
            request_list.append("json=json_dict")

        request_str = ""
        if len(request_list):
            request_str = ", " + ", ".join(request_list)

        func_tail = f"""        return self._send_request(uri=f"{uri}", 
        method="{method.upper()}"{request_str})\n"""

        return func_header + func_body + func_tail, use_list

    @staticmethod
    def _get_api_header(class_name: str, import_list: bool) -> str:
        """
        Generate the header code for the API class.

        Args:
            class_name (str): The name of the API class.
            import_list (bool): Indicates whether List is used in the functions.

        Returns:
            str: The generated header code.
        """
        partial_str = ""
        if import_list:
            partial_str = ", List"
        header_str = "# -*- coding: utf-8 -*-\n"
        header_str += f"from typing import Dict, Any{partial_str}\n"
        header_str += "from api.base_api import BaseAPI\n\n\n"
        header_str += f"class {class_name}(BaseAPI):\n"

        return header_str

    @staticmethod
    def _write_api_file(module: str, module_code: str) -> None:
        """
        Write the generated API code to a file.

        Args:
            module (str): The name of the module.
            module_code (str): The generated API code.

        Returns:
            None
        """
        api_dir = os.path.abspath(os.path.join(utils_dir, f"../tmp/api/{module}"))
        api_path = os.path.abspath(os.path.join(api_dir, f"{module}_api.py"))
        formatted_code = black.format_str(module_code, mode=black.FileMode())
        with open(api_path, "w+", encoding="utf-8") as f:
            f.write(formatted_code)
        init_path = os.path.abspath(os.path.join(api_dir, f"__init__.py"))
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("# -*- coding: utf-8 -*-\n")

    @staticmethod
    def _generate_api_templates(swagger_dict: dict) -> None:
        """
        Generate API templates based on Swagger data and write them to files.

        Args:
            swagger_dict (dict): Swagger data.

        Returns:
            None
        """
        for module in swagger_dict.keys():
            module_code = ""
            import_list = False
            for api in swagger_dict[module]:
                func_code, use_list = SwaggerParser._get_api_func(api)
                if use_list:
                    import_list = True
                module_code += func_code
            module_code = SwaggerParser._get_api_header(SwaggerParser._snake_to_pascal(module) + "API",
                                                        import_list) + module_code
            SwaggerParser._write_api_file(module, module_code)

    @staticmethod
    def _get_conf_code(module: str) -> str:
        """
        Generate conftest.py code for the specified module.

        Args:
            module (str): The name of the module.

        Returns:
            str: The generated conftest.py code.
        """
        api_cls = f"{SwaggerParser._snake_to_pascal(module)}API"
        conf_code = ""
        conf_code += "# -*- coding: utf-8 -*-\n"
        conf_code += "import pytest\n"
        conf_code += "from config.conf import Global\n"
        conf_code += f"from tmp.api.{module}.{module}_api import {api_cls}\n\n\n"
        conf_code += f"""@pytest.fixture(scope="package")\n"""
        conf_code += f"def {module}_api():\n"
        conf_code += f"    {module}_api = {api_cls}(base_url=Global.constants.BASE_URL, " \
                     f"headers=Global.constants.HEADERS)\n"
        conf_code += f"    return {module}_api\n"
        return conf_code

    @staticmethod
    def _write_conf_file(module: str, conf_code: str) -> None:
        """
        Write the generated conftest.py code to a file.

        Args:
            module (str): The name of the module.
            conf_code (str): The generated conftest.py code.

        Returns:
            None
        """
        testcases_dir = os.path.abspath(os.path.join(utils_dir, f"../tmp/testcases/{module}"))
        conf_path = os.path.abspath(os.path.join(testcases_dir, "conftest.py"))
        formatted_code = black.format_str(conf_code, mode=black.FileMode())
        with open(conf_path, "w+", encoding="utf-8") as f:
            f.write(formatted_code)
        init_path = os.path.abspath(os.path.join(testcases_dir, f"__init__.py"))
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("# -*- coding: utf-8 -*-\n")

    @staticmethod
    def _get_testcases_code(module: str, api: dict) -> Tuple[str, str]:
        """
        Generate test function code for the specified API.

        Args:
            module (str): The name of the module.
            api (dict): Swagger API details.

        Returns:
            Tuple[str, str]: The generated test function code and the file name.
        """
        header_code = ""
        header_code += "# -*- coding: utf-8 -*-\n"
        header_code += "import allure\n"
        header_code += "import pytest\n"
        header_code += "from utils.logger import logger\n"
        header_code += "from utils.common import set_assertion_error\n\n\n"

        testcases_code = ""
        testcases_code += "@allure.severity(\"normal\")\n"
        testcases_code += "@pytest.mark.normal\n"

        method = api["method"]
        snake_name = SwaggerParser._pascal_to_snake(api["detail"]["operationId"])
        if snake_name.startswith(method):
            api_func_name = snake_name
            test_func_name = f"test_{api_func_name}"
        else:
            api_func_name = f"""{method}_{SwaggerParser._pascal_to_snake(api["detail"]["operationId"])}"""
            test_func_name = f"""test_{api_func_name}"""

        words = test_func_name.split("_")
        words.pop(1)
        file_name = "_".join(words)

        params = api["detail"].get("parameters", [])
        if params:
            params = SwaggerParser._get_deduplicated_params(params)
            params = [param for param in params if param["required"]]

        name_list = []
        for param in params:
            param_name = SwaggerParser._pascal_to_snake(param["name"])
            param_name = SwaggerParser._avoid_keywords(param_name)
            name_list.append(param_name)
            testcases_code += f"""@pytest.mark.parametrize("{param_name}", [None])\n"""

        param_str = (", " + ", ".join(name_list)) if name_list else ""
        testcases_code += f"def {test_func_name}({module}_api{param_str}):\n"

        param_str = ", ".join([f"{name}={name}" for name in name_list]) if name_list else ""
        testcases_code += f"    res = {module}_api.{api_func_name}({param_str})\n"
        testcases_code += "    actual_code = res[\"status_code\"]\n"
        testcases_code += "    logger.info(f\"%s status code: {actual_code}\")\n\n" % api_func_name
        testcases_code += "    expected_code = 200\n"
        testcases_code += "    assert actual_code == expected_code, \
                            set_assertion_error(f\"actual: {actual_code}, expected: {expected_code}\")\n"

        testcases_code = header_code + testcases_code

        return testcases_code, file_name

    @staticmethod
    def _write_testcases_file(module: str, file_name: str, testcases_code: str) -> None:
        """
        Write the generated test function code to a file.

        Args:
            module (str): The name of the module.
            file_name (str): The name of the file.
            testcases_code (str): The generated test function code.

        Returns:
            None
        """
        testcases_dir = os.path.abspath(os.path.join(utils_dir, f"../tmp/testcases/{module}"))
        testcases_path = os.path.abspath(os.path.join(testcases_dir, f"{file_name}.py"))
        formatted_code = black.format_str(testcases_code, mode=black.FileMode())
        with open(testcases_path, "w+", encoding="utf-8") as f:
            f.write(formatted_code)

    @staticmethod
    def _generate_testcases_templates(swagger_dict: dict) -> None:
        """
        Generate test function templates based on Swagger data and write them to files.

        Args:
            swagger_dict (dict): Swagger data.

        Returns:
            None
        """
        for module in swagger_dict.keys():
            conf_code = SwaggerParser._get_conf_code(module)
            SwaggerParser._write_conf_file(module, conf_code)
            for api in swagger_dict[module]:
                testcases_code, file_name = SwaggerParser._get_testcases_code(module, api)
                SwaggerParser._write_testcases_file(module, file_name, testcases_code)

    def generate_templates(self) -> None:
        """
        Generate API and test function templates based on Swagger data.

        Returns:
            None
        """
        SwaggerParser._clear_tmp_dir()
        swagger_dict = self._get_swagger_dict()
        SwaggerParser._generate_api_templates(swagger_dict)
        SwaggerParser._generate_testcases_templates(swagger_dict)
        logger.info(f"""template dir: {os.path.abspath(os.path.join(utils_dir, "../tmp"))}""")


if __name__ == "__main__":
    # swagger_url is the link to the swagger api-docs
    SwaggerParser(swagger_url="").generate_templates()
