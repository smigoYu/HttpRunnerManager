import os

from django.core.exceptions import ObjectDoesNotExist

from ApiManager.models import TestCaseInfo, ModuleInfo, ProjectInfo, DebugTalk
from ApiManager.utils.testcase import _dump_python_file, _dump_yaml_file


def run_by_single(index, base_url, path, config_id=None):
    """
    加载单个case用例信息
    :param index: int or str：用例索引
    :param base_url: str：环境地址
    :param config_id: str or int：配置索引
    :return: dict
    """
    config = {
        'config': {
            'name': 'base_url config',
            'request': {
                'base_url': base_url
            }
        }
    }
    testcase_list = []

    testcase_list.append(config)

    config_id = None if config_id == '' else config_id
    if config_id != None:  # 指定了配置
        try:
            config_request = eval(TestCaseInfo.objects.get(id=config_id).request)
        except ObjectDoesNotExist:
            return testcase_list
        config_request.get('config').get('request').setdefault('base_url', base_url)
        testcase_list[0] = config_request
    try:
        obj = TestCaseInfo.objects.get(id=index)
    except ObjectDoesNotExist:
        return testcase_list

    include = eval(obj.include)
    request = eval(obj.request)
    name = obj.name

    project = obj.belong_project
    module = obj.belong_module.module_name

    testcase_dir_path = os.path.join(path, project)

    if not os.path.exists(testcase_dir_path):
        os.makedirs(testcase_dir_path)

        try:
            debugtalk = DebugTalk.objects.get(belong_project__project_name=project).debugtalk
        except ObjectDoesNotExist:
            debugtalk = ''

        _dump_python_file(os.path.join(testcase_dir_path, '__init__.py'), '')
        _dump_python_file(os.path.join(testcase_dir_path, 'debugtalk.py'), debugtalk)

    testcase_dir_path = os.path.join(testcase_dir_path, module)

    if not os.path.exists(testcase_dir_path):
        os.mkdir(testcase_dir_path)

    for test_info in include:
        try:
            if isinstance(test_info, dict) and config_id == None:
                config_id = test_info.pop('config')[0]
                config_request = eval(TestCaseInfo.objects.get(id=config_id).request)
                config_request.get('config').get('request').setdefault('base_url', base_url)
                testcase_list[0] = config_request
            elif not isinstance(test_info, dict):
                id = test_info[0]
                pre_request = eval(TestCaseInfo.objects.get(id=id).request)
                testcase_list.append(pre_request)

        except ObjectDoesNotExist:
            return testcase_list

    testcase_list.append(request)

    _dump_yaml_file(os.path.join(testcase_dir_path, name + '.yml'), testcase_list)

def run_by_batch(test_list, base_url, path, config=None, type=None, mode=False):
    """
    批量组装用例数据
    :param test_list:
    :param base_url: str: 环境地址
    :param type: str：用例级别
    :param mode: boolean：True 异步 False: 同步
    :return: list
    """

    if mode:
        for index in range(len(test_list) - 3):
            form_test = test_list[index].split('=')
            value = form_test[1]
            if type == 'project':
                run_by_project(value, base_url, path, config)
            elif type == 'module':
                run_by_module(value, base_url, path, config)

    else:
        if type == 'project':
            for value in test_list.values():
                run_by_project(value, base_url, path, config)
        elif type == 'module':
            for value in test_list.values():
                run_by_module(value, base_url, path, config)
        else:

            for index in range(len(test_list) - 2):
                form_test = test_list[index].split('=')
                index = form_test[1]
                run_by_single(index, base_url, path, config)


def run_by_module(id, base_url, path, config=None):
    """
    组装模块用例
    :param id: int or str：模块索引
    :param base_url: str：环境地址
    :return: list
    """
    obj = ModuleInfo.objects.get(id=id)
    test_index_list = TestCaseInfo.objects.filter(belong_module=obj, type=1).values_list('id')
    for index in test_index_list:
        run_by_single(index[0], base_url, path, config)


def run_by_project(id, base_url, path, config=None):
    """
    组装项目用例
    :param id: int or str：项目索引
    :param base_url: 环境地址
    :return: list
    """
    obj = ProjectInfo.objects.get(id=id)
    module_index_list = ModuleInfo.objects.filter(belong_project=obj).values_list('id')
    for index in module_index_list:
        module_id = index[0]
        run_by_module(module_id, base_url, path, config)
