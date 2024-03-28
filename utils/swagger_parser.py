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
import traceback
from config.conf import Global
from utils.logger import logger
from typing import Tuple, Union
from utils.dirs import utils_dir


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
        self._paths_dict = None
        self._definitions_dict = None

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

    def _get_swagger_data(self) -> dict:
        """
        Get Swagger JSON data by making a request to the specified Swagger URL.

        Returns:
            dict: Path data of swagger.

        Raises:
            ValueError: If the Swagger URL response is not a valid JSON.
        """
        try:
            response = requests.get(self._swagger_url, headers=Global.constants.HEADERS)
        except Exception as e:
            logger.error(f"{e}\n{traceback.format_exc()}")
            sys.exit(1)

        if response.status_code == 200:
            try:
                response.json()
            except ValueError:
                logger.error(f"Parse Swagger docs error: {response.text}")
                sys.exit(1)
            else:
                self._definitions_dict = response.json().get("definitions", dict())
                return response.json().get("paths", dict())
        else:
            logger.error("Cannot request Swagger URL")
            sys.exit(1)

    def _process_swagger_data(self) -> None:
        """
        Processed path data of swagger.

        Returns:
            None
        """
        raw_paths_dict = self._get_swagger_data()
        paths_dict = {}
        for path, path_details in raw_paths_dict.items():
            for api_method, api_detail in path_details.items():
                module_name = SwaggerParser._pascal_to_snake(api_detail["tags"][0])
                SwaggerParser._create_package_dir(module_name)
                api = {"uri": path, "method": api_method, "detail": api_detail}
                if module_name in paths_dict.keys():
                    paths_dict[module_name].append(api)
                else:
                    paths_dict[module_name] = []
                    paths_dict[module_name].append(api)

        self._paths_dict = paths_dict

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
            if param.get("schema") is None:
                param.update({"use_schema": True})
            else:
                param.update({"use_schema": False})
            snake_name = SwaggerParser._pascal_to_snake(param["name"])
            if snake_name not in snake_names:
                deduplicated_params.append(param)
                snake_names.append(snake_name)

        return deduplicated_params

    @staticmethod
    def _get_wrapped_string(long_string: str, indent: int, param_process: bool = False) -> str:
        """
        Generate wrapped string by splitting a long string into smaller segments.

        Args:
            long_string (str): The long string to be split.
            indent (int, optional): The number of spaces to indent each segment.
            param_process (bool, optional): Whether to process parameter description. Defaults to False.

        Returns:
            str: The wrapped string with each segment smaller than the specified length.
        """
        length = 116 - indent
        if param_process:
            string_list = long_string.split(": ", 1)
            key_string = string_list[0]
            value_string = string_list[-1]
            value_string = value_string.replace(":", " - ")
            value_string = re.sub(r"([,;])(?!\s)", r"\1 ", value_string)
            long_string = f"{key_string}: {value_string}"
        else:
            long_string = re.sub(r"([,;])(?!\s)", r"\1 ", long_string)

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

        return " " * indent + f"""\n{" " * indent}""".join(wrapped_strings)

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

    def _generate_sample_data(self, schema: dict) -> Union[None, dict, list, int, str]:
        """
        Generate sample data based on the given schema.

        Args:
            schema (dict): The schema to generate sample data from.

        Returns:
            Union[None, dict, list, int, str]: The generated sample data.
        """
        if schema is None:
            return None
        if schema.get("type") == "object":
            sample_data = {}
            for prop, prop_schema in schema.get("properties", {}).items():
                sample_data[prop] = self._generate_sample_data(prop_schema)
            return sample_data
        elif schema.get("type") == "array":
            return [self._generate_sample_data(schema["items"])]
        elif schema.get("type") == "integer":
            return 0
        elif schema.get("type") == "string":
            return ""
        elif schema.get("type") == "boolean":
            return False
        elif schema.get("$ref"):
            return self._generate_sample_data(self._definitions_dict.get(schema.get("$ref").split("/")[-1]))
        else:
            return None

    def _get_api_func(self, api: dict) -> Tuple[str, bool]:
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

        logger.debug(json.dumps(api["detail"]))

        summary = api["detail"].get("summary", "Null")
        summary = SwaggerParser._get_wrapped_string(summary, indent=8)

        uri = SwaggerParser._convert_path_params(api["uri"])

        params = api["detail"].get("parameters", [])
        if params:
            params = SwaggerParser._get_deduplicated_params(params)
            params = sorted(params, key=lambda x: x["required"], reverse=True)
            params = sorted(params, key=lambda x: x["use_schema"], reverse=True)

        params_list = []
        params_dict = {}
        header_dict = {}
        data_dict = {}
        json_dict = {}
        schema_dict = {}
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
                          if param["required"] and param.get("schema") is None
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

            if param.get("schema"):
                schema_dict.update({param["name"]: param.get("schema")})

        params_header = ""
        if params_list:
            params_header = (", " +
                             ", ".join(
                                 [f"""{next(iter(item.keys()))}: {item[next(iter(item.keys()))]["type"]}"""
                                  for item in params_list]))
        func_header = f"""\n    def {func_name}(self{params_header}) -> Dict[str, Any]:\n"""

        func_body = "        \"\"\"\n%s\n" % summary
        if params_list:
            func_body += "\n        Args:\n"
        for item in params_list:
            desc_string = f"""{next(iter(item.keys()))} ({item[next(iter(item.keys()))]["type"]}): """ + \
                          item[next(iter(item.keys()))]["desc"]
            func_body += f"""{SwaggerParser._get_wrapped_string(desc_string, indent=12, param_process=True)}\n"""
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
            if len(schema_dict.keys()) == 1 and schema_dict.keys() == json_dict.keys():
                for k, v in json_dict.items():
                    schema_sample = self._generate_sample_data(schema_dict.get(k))
                    if schema_sample == "":
                        schema_sample = "\"\""
                    func_body += f"""        {v}_sample = {schema_sample}\n"""
                    func_body += f"""        json_dict = {v} if {v} else {v}_sample\n"""
            else:
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
        with open(api_path, "w", encoding="utf-8") as f:
            f.write(formatted_code)
        init_path = os.path.abspath(os.path.join(api_dir, f"__init__.py"))
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("# -*- coding: utf-8 -*-\n")

    def _generate_api_templates(self) -> None:
        """
        Generate API templates based on Swagger data and write them to files.

        Returns:
            None
        """
        for module in self._paths_dict.keys():
            module_code = ""
            import_list = False
            for api in self._paths_dict[module]:
                func_code, use_list = self._get_api_func(api)
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
        with open(conf_path, "w", encoding="utf-8") as f:
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
        with open(testcases_path, "w", encoding="utf-8") as f:
            f.write(formatted_code)

    def _generate_testcases_templates(self) -> None:
        """
        Generate test function templates based on Swagger data and write them to files.

        Returns:
            None
        """
        for module in self._paths_dict.keys():
            conf_code = SwaggerParser._get_conf_code(module)
            SwaggerParser._write_conf_file(module, conf_code)
            for api in self._paths_dict[module]:
                testcases_code, file_name = SwaggerParser._get_testcases_code(module, api)
                SwaggerParser._write_testcases_file(module, file_name, testcases_code)

    def generate_templates(self) -> None:
        """
        Generate API and test function templates based on Swagger data.

        Returns:
            None
        """
        SwaggerParser._clear_tmp_dir()
        self._process_swagger_data()
        self._generate_api_templates()
        self._generate_testcases_templates()
        logger.info(f"""templates are generated in: {os.path.abspath(os.path.join(utils_dir, "../tmp"))}""")


if __name__ == "__main__":
    # swagger_url is the link to the swagger api-docs
    SwaggerParser(swagger_url="").generate_templates()
