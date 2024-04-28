# -*- coding: utf-8 -*-
import builtins
import keyword
import os
import re
import shutil
import sys
import traceback
from typing import Tuple, Union

import black
import isort
import requests

from config.conf import Global
from utils.dirs import template_dir
from utils.logger import logger


class SwaggerParser:
    def __init__(self, swagger_url: str) -> None:
        """
        Initialize the class.

        Args:
            swagger_url (str): The url of the swagger docs.

        Returns:
            None
        """
        self._swagger_url = swagger_url
        self._swagger_dict = None
        self._paths_dict = None
        self._api_dir = os.path.abspath(os.path.join(template_dir, "api"))
        self._testcases_dir = os.path.abspath(os.path.join(template_dir, "testcases"))

    @staticmethod
    def _pascal_to_snake(name: str) -> str:
        """
        Converts pascal case to snake case.

        Args:
            name (str): The input pascal case string.

        Returns:
            str: The converted snake case string.
        """
        words = re.findall(r"[A-Z]+[a-z\d]*|[a-z]+\d*", name)
        return "_".join(word.lower() for word in words)

    @staticmethod
    def _snake_to_pascal(name: str) -> str:
        """
        Converts snake case to pascal case.

        Args:
            name (str): The input snake case string.

        Returns:
            str: The converted pascal case string.
        """
        words = name.split("_")
        return "".join(word.capitalize() for word in words)

    @staticmethod
    def _convert_path_params(path: str) -> str:
        """
        Convert swagger path parameters to snake case.

        Args:
            path (str): The swagger API path.

        Returns:
            str: The converted path with parameters in snake case.
        """
        matches = re.findall(r"{(.*?)}", path)
        for match in matches:
            path = path.replace(
                "{%s}" % match,
                "{%s}"
                % SwaggerParser._avoid_keywords(SwaggerParser._pascal_to_snake(match)),
            )
        return path

    @staticmethod
    def _get_wrapped_string(
        long_string: str, indent: int, param_process: bool = False
    ) -> str:
        """
        Generate wrapped string by splitting a long string into smaller segments.

        Args:
            long_string (str): The long string to be split.
            indent (int, optional): The number of spaces to indent each segment.
            param_process (bool, optional): Whether to process parameter description. Defaults to False.

        Returns:
            str: The wrapped string with each segment smaller than the specified length.
        """
        length = 110 - indent
        if param_process:
            string_list = long_string.split(": ", 1)
            key_string = string_list[0]
            value_string = re.sub(
                r"([,;])(?!\s)", r"\1 ", string_list[-1].replace(":", " - ")
            )
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
    def _process_params(params: list) -> list:
        """
        Process parameters.

        Args:
            params (list): List of swagger API parameters.

        Returns:
            list: Processed list of swagger API parameters.
        """
        params.reverse()

        processed_params = []
        snake_names = []
        for param in params:
            if not param.get("name"):
                continue

            param_type = param.pop("type", None)
            if param_type:
                param.update({"schema": {"type": param_type}})

                param_items = param.pop("items", None)
                if param_items:
                    param.get("schema").update({"items": param_items})

            if not param.get("schema"):
                param.update({"schema": {"type": "Any"}})

            if not param.get("schema").get("type"):
                param.get("schema").update({"type": "object"})

            if not param.get("required"):
                param.update({"required": False})

            snake_name = SwaggerParser._pascal_to_snake(param.get("name"))
            if snake_name not in snake_names:
                processed_params.append(param)
                snake_names.append(snake_name)

        processed_params = sorted(
            processed_params,
            key=lambda x: x.get("required"),
            reverse=True,
        )

        return processed_params

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
            "int": "int",
            "long": "int",
            "boolean": "bool",
            "array": "list",
            "list": "list",
            "object": "dict",
        }
        return python_type_mapping.get(java_type.lower(), "Any")

    def _generate_sample_data(self, schema: dict) -> Union[dict, list, int, str]:
        """
        Generate sample data based on the given schema.

        Args:
            schema (dict): The schema to generate sample data from.

        Returns:
            Union[dict, list, int, str]: The generated sample data.
        """
        if not schema:
            return {}

        if schema.get("type") == "array":
            return [self._generate_sample_data(schema.get("items"))]
        elif schema.get("type") == "integer":
            return 0
        elif schema.get("type") == "string":
            return ""
        elif schema.get("type") == "boolean":
            return False
        elif schema.get("$ref"):
            keys = schema.get("$ref").split("/")[1:]
            sub_schema = self._swagger_dict
            for key in keys:
                sub_schema = sub_schema.get(key)
            return self._generate_sample_data(schema=sub_schema)
        elif schema.get("type") == "object":
            sample_data = {}
            for prop, prop_schema in schema.get("properties", {}).items():
                sample_data[prop] = self._generate_sample_data(prop_schema)
            if schema.get("additionalProperties"):
                sample_data[""] = self._generate_sample_data(
                    schema.get("additionalProperties", {})
                )
            return sample_data
        else:
            return {}

    def _write_testcases_file(
        self, module: str, file_name: str, testcases_code: str
    ) -> None:
        """
        Write the generated testcases code to a file.

        Args:
            module (str): The name of the module.
            file_name (str): The name of the file.
            testcases_code (str): The generated testcases code.

        Returns:
            None
        """
        module_dir = os.path.abspath(os.path.join(self._testcases_dir, module))

        formatted_code = black.format_str(testcases_code, mode=black.FileMode())
        formatted_code = isort.code(
            formatted_code,
            config=isort.Config(
                profile="black", known_first_party=["api", "config", "utils"]
            ),
        )
        with open(
            os.path.abspath(os.path.join(module_dir, f"{file_name}.py")),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(formatted_code)

    @staticmethod
    def _get_testcases_code(module: str, api: dict) -> Tuple[str, str]:
        """
        Generate test function code for the specified API.

        Args:
            module (str): The name of the module.
            api (dict): swagger API details.

        Returns:
            Tuple[str, str]: The generated test function code and the file name.
        """
        header_code = ""
        header_code += "# -*- coding: utf-8 -*-\n"
        header_code += "import allure\n"
        header_code += "import pytest\n"
        header_code += "from utils.logger import logger\n"
        header_code += "from utils.common import set_allure_detail\n\n\n"

        method = api.get("method")
        uri = api.get("uri")
        detail = api.get("detail")

        api_name = f"{method}_{SwaggerParser._pascal_to_snake(uri)}"
        test_name = f"test_{api_name}"
        params = detail.get("parameters", [])

        request_body = detail.get("requestBody", {})
        if request_body:
            params.append(
                {
                    "in": "body",
                    "name": "request_body",
                    "required": request_body.get("required", False),
                    "description": request_body.get("description", "request body"),
                    "schema": request_body.get("content")
                    .get("application/json")
                    .get("schema"),
                }
            )

        params = SwaggerParser._process_params(params)
        params = [param for param in params if param.get("required")]

        testcases_code = ""
        testcases_code += f"class {SwaggerParser._snake_to_pascal(test_name)}:\n"
        testcases_code += """    @allure.severity(\"critical\")\n"""
        testcases_code += "    @pytest.mark.critical\n"
        testcases_code += "    @pytest.mark.smoke\n"
        testcases_code += f"    @pytest.mark.{api_name}\n"

        name_list = []
        for param in params:
            param_name = SwaggerParser._avoid_keywords(
                SwaggerParser._pascal_to_snake(param.get("name"))
            )
            name_list.append(param_name)
            testcases_code += (
                f"""    @pytest.mark.parametrize("{param_name}", [None])\n"""
            )

        param_str = (", " + ", ".join(name_list)) if name_list else ""
        testcases_code += f"    def {test_name}(self, {module}_api{param_str}):\n"

        param_str = (
            ", ".join([f"{name}={name}" for name in name_list]) if name_list else ""
        )
        testcases_code += f"        res = {module}_api.{api_name}({param_str})\n"
        testcases_code += """        actual_code = res[\"status_code\"]\n"""
        testcases_code += (
            """        logger.info(f\"%s status code: {actual_code}\")\n\n""" % api_name
        )
        testcases_code += "        expected_code = 200\n"
        testcases_code += """        assert actual_code == expected_code, \
                                set_allure_detail(f\"actual: {actual_code}, expected: {expected_code}\")\n"""

        testcases_code = header_code + testcases_code

        return testcases_code, test_name

    def _write_conftest_file(self, module: str, conftest_code: str) -> None:
        """
        Write the generated conftest code to a file.

        Args:
            module (str): The name of the module.
            conftest_code (str): The generated conftest code.

        Returns:
            None
        """
        module_dir = os.path.abspath(os.path.join(self._testcases_dir, module))

        formatted_code = black.format_str(conftest_code, mode=black.FileMode())
        formatted_code = isort.code(
            formatted_code,
            config=isort.Config(
                profile="black", known_first_party=["api", "config", "utils"]
            ),
        )
        with open(
            os.path.abspath(os.path.join(module_dir, "conftest.py")),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(formatted_code)

        with open(
            os.path.abspath(os.path.join(module_dir, "__init__.py")),
            "w",
            encoding="utf-8",
        ) as f:
            f.write("# -*- coding: utf-8 -*-\n")

    @staticmethod
    def _get_conftest_code(module: str) -> str:
        """
        Generate conftest code for the specified module.

        Args:
            module (str): The name of the module.

        Returns:
            str: The generated conftest code.
        """
        api_cls = f"{SwaggerParser._snake_to_pascal(module)}API"
        conftest_code = ""
        conftest_code += "# -*- coding: utf-8 -*-\n"
        conftest_code += "import pytest\n"
        conftest_code += "from config.conf import Global\n"
        conftest_code += (
            f"from template.api.{module}.{module}_api import {api_cls}\n\n\n"
        )
        conftest_code += """@pytest.fixture(scope="package")\n"""
        conftest_code += f"def {module}_api():\n"
        conftest_code += (
            f"    return {api_cls}(base_url=Global.CONSTANTS.BASE_URL, "
            "headers=Global.CONSTANTS.HEADERS)\n"
        )
        return conftest_code

    def _generate_testcases_templates(self) -> None:
        """
        Generate testcases templates based on swagger and write them to files.

        Returns:
            None
        """
        for module in self._paths_dict.keys():
            conftest_code = SwaggerParser._get_conftest_code(module)
            self._write_conftest_file(module, conftest_code)
            for api in self._paths_dict[module]:
                testcases_code, file_name = SwaggerParser._get_testcases_code(
                    module, api
                )
                self._write_testcases_file(module, file_name, testcases_code)

    def _write_api_file(self, module: str, api_code: str) -> None:
        """
        Write the generated api code to a file.

        Args:
            module (str): The name of the module.
            api_code (str): The generated api code.

        Returns:
            None
        """
        module_dir = os.path.abspath(os.path.join(self._api_dir, module))

        formatted_code = black.format_str(api_code, mode=black.FileMode())
        formatted_code = isort.code(
            formatted_code,
            config=isort.Config(
                profile="black", known_first_party=["api", "config", "utils"]
            ),
        )
        with open(
            os.path.abspath(os.path.join(module_dir, f"{module}_api.py")),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(formatted_code)

        with open(
            os.path.abspath(os.path.join(module_dir, "__init__.py")),
            "w",
            encoding="utf-8",
        ) as f:
            f.write("# -*- coding: utf-8 -*-\n")

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

    def _get_api_func(self, api: dict) -> Tuple[str, bool]:
        """
        Generate API function code based on swagger API details.

        Args:
            api (dict): swagger API details.

        Returns:
            Tuple[str, bool]: The api function code and a boolean indicating whether List is used in the function.
        """
        method = api.get("method")
        uri = api.get("uri")
        detail = api.get("detail")

        api_name = f"{method}_{SwaggerParser._pascal_to_snake(uri)}"
        converted_uri = SwaggerParser._convert_path_params(uri)
        summary = SwaggerParser._get_wrapped_string(
            detail.get("summary", "Null"), indent=8
        )
        params = detail.get("parameters", [])

        request_body = detail.get("requestBody", {})
        if request_body:
            params.append(
                {
                    "in": "body",
                    "name": "request_body",
                    "required": request_body.get("required", False),
                    "description": request_body.get("description", "request body"),
                    "schema": request_body.get("content")
                    .get("application/json")
                    .get("schema"),
                }
            )

        params = SwaggerParser._process_params(params)

        params_list = []
        params_dict = {}
        header_dict = {}
        data_dict = {}
        json_dict = {}
        params_schema_dict = {}
        json_schema_dict = {}
        use_list = False
        for param in params:
            param_name = SwaggerParser._avoid_keywords(
                SwaggerParser._pascal_to_snake(param.get("name"))
            )
            param_schema = param.get("schema")
            param_type = SwaggerParser._get_python_type(param_schema.get("type"))

            if param_type == "list":
                if param_schema.get("items", {}).get("$ref"):
                    list_inner_type = "dict"
                else:
                    list_inner_type = SwaggerParser._get_python_type(
                        param_schema.get("items", {}).get("type", "Any")
                    )

                param_type = f"List[{list_inner_type}]"
                use_list = True

            param_desc = param.get("description", "null")
            param_item = (
                {param_name: {"type": param_type, "desc": param_desc}}
                if param.get("required")
                else {param_name: {"type": f"{param_type} = None", "desc": param_desc}}
            )
            params_list.append(param_item)

            if param.get("in", "body") == "query":
                params_dict.update({param.get("name"): param_name})
                if param.get("schema"):
                    params_schema_dict.update({param.get("name"): param.get("schema")})
            elif param.get("in", "body") == "header":
                header_dict.update({param.get("name"): param_name})
            elif param.get("in", "body") == "formData":
                data_dict.update({param.get("name"): param_name})
            elif param.get("in", "body") == "body":
                json_dict.update({param.get("name"): param_name})
                if param.get("schema"):
                    json_schema_dict.update({param.get("name"): param.get("schema")})

        params_header = ""
        if params_list:
            params_header = ", " + ", ".join(
                [
                    f"""{next(iter(item.keys()))}: {item[next(iter(item.keys()))].get("type")}"""
                    for item in params_list
                ]
            )
        func_header = f"\n    def {api_name}(self{params_header}) -> Dict[str, Any]:\n"

        func_body = """        \"\"\"\n%s\n""" % summary
        if params_list:
            func_body += "\n        Args:\n"
        for item in params_list:
            desc_string = f"""{next(iter(item.keys()))} ({item[next(iter(item.keys()))].get("type")}): """ + item[
                next(iter(item.keys()))
            ].get(
                "desc"
            )
            func_body += f"{SwaggerParser._get_wrapped_string(desc_string, indent=12, param_process=True)}\n"

        func_body += (
            "\n        Returns:\n            Dict[str, Any]: "
            "The response content of the request as a dictionary."
            """\n        \"\"\"\n"""
        )

        request_list = []
        if params_dict:
            schema_type = next(iter(params_schema_dict.values())).get("type")
            if (
                len(params_schema_dict.keys()) == 1
                and params_schema_dict.keys() == params_dict.keys()
                and (schema_type == "object" or schema_type == "array")
            ):
                for k, v in params_dict.items():
                    schema_sample = self._generate_sample_data(
                        params_schema_dict.get(k)
                    )
                    if schema_sample == "":
                        schema_sample = """\"\""""
                    func_body += f"        {v}_sample = {schema_sample}\n"
                    func_body += f"        params_dict = {v} if {v} else {v}_sample\n"
            else:
                partial_str = ", ".join(
                    [f""""{k}": {v}""" for k, v in params_dict.items()]
                )
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
            schema_type = next(iter(json_schema_dict.values())).get("type")
            if (
                len(json_schema_dict.keys()) == 1
                and json_schema_dict.keys() == json_dict.keys()
                and (schema_type == "object" or schema_type == "array")
            ):
                for k, v in json_dict.items():
                    schema_sample = self._generate_sample_data(json_schema_dict.get(k))
                    if schema_sample == "":
                        schema_sample = """\"\""""
                    func_body += f"        {v}_sample = {schema_sample}\n"
                    func_body += f"        json_dict = {v} if {v} else {v}_sample\n"
            else:
                partial_str = ", ".join(
                    [f""""{k}": {v}""" for k, v in json_dict.items()]
                )
                func_body += """        json_dict = {%s}\n""" % partial_str
            request_list.append("json=json_dict")

        request_str = ""
        if len(request_list):
            request_str = ", " + ", ".join(request_list)

        func_tail = (
            f"""        return self._send_request(uri=f"{converted_uri}", """
            f"""method="{method.upper()}"{request_str})\n"""
        )

        return func_header + func_body + func_tail, use_list

    def _generate_api_templates(self) -> None:
        """
        Generate api templates based on swagger and write them to files.

        Returns:
            None
        """
        for module in self._paths_dict.keys():
            api_code = ""
            import_list = False
            for api in self._paths_dict[module]:
                func_code, use_list = self._get_api_func(api)
                if use_list:
                    import_list = True
                api_code += func_code
            api_code = (
                SwaggerParser._get_api_header(
                    SwaggerParser._snake_to_pascal(module) + "API", import_list
                )
                + api_code
            )
            self._write_api_file(module, api_code)

    def _create_package_dir(self, name: str) -> None:
        """
        Creates package directories for api and testcases.

        Args:
            name (str): The name of the package.

        Returns:
            None
        """
        init_dir = os.path.abspath(os.path.join(self._api_dir, name))
        os.makedirs(init_dir, exist_ok=True)

        init_path = os.path.abspath(os.path.join(init_dir, "__init__.py"))
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("# -*- coding: utf-8 -*-\n")

        init_dir = os.path.abspath(os.path.join(self._testcases_dir, name))
        os.makedirs(init_dir, exist_ok=True)

        init_path = os.path.abspath(os.path.join(init_dir, "__init__.py"))
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("# -*- coding: utf-8 -*-\n")

    def _reformat_paths_dict(self) -> None:
        """
        Reformatted swagger paths dict.

        Returns:
            None
        """
        raw_paths_dict = self._swagger_dict.get("paths", {})
        paths_dict = {}
        for path, path_details in raw_paths_dict.items():
            for api_method, api_detail in path_details.items():
                module_name = SwaggerParser._pascal_to_snake(api_detail.get("tags")[-1])
                self._create_package_dir(module_name)

                api = {"uri": path, "method": api_method, "detail": api_detail}
                if module_name in paths_dict.keys():
                    paths_dict[module_name].append(api)
                else:
                    paths_dict[module_name] = []
                    paths_dict[module_name].append(api)

        self._paths_dict = paths_dict

    def _get_swagger_data(self) -> None:
        """
        Get swagger json data by making a request to the specified swagger docs url.

        Returns:
            None
        """
        response = requests.get(self._swagger_url, headers=Global.CONSTANTS.HEADERS)

        if response.status_code == 200:
            self._swagger_dict = response.json()
        else:
            logger.error("cannot request swagger url")
            sys.exit(1)

    @staticmethod
    def _clear_template_dir() -> None:
        """
        Clears the template directory.

        Returns:
            None
        """
        if os.path.exists(template_dir):
            shutil.rmtree(template_dir)

        os.makedirs(template_dir, exist_ok=True)

        with open(
            os.path.abspath(os.path.join(template_dir, "__init__.py")),
            "w",
            encoding="utf-8",
        ) as f:
            f.write("# -*- coding: utf-8 -*-\n")

    def generate_templates(self) -> None:
        """
        Generate API and test function templates based on swagger data.

        Returns:
            None
        """
        SwaggerParser._clear_template_dir()
        self._get_swagger_data()
        self._reformat_paths_dict()
        self._generate_api_templates()
        self._generate_testcases_templates()
        logger.info(f"templates are generated to {template_dir}")


if __name__ == "__main__":
    try:
        # swagger_url is the link to the swagger v2/v3 api-docs
        SwaggerParser(swagger_url="").generate_templates()
    except Exception as e:
        logger.error(f"{e}\n{traceback.format_exc()}")
