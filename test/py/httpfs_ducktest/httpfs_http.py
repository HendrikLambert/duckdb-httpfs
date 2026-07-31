import shutil

from ducktest import use_service
from ducktest.resources.httpserver import HTTPSERVER_SERVICE

from .remote_data import prepare_remote_data


def httpfs_http_populate(block, config):
    data_dir = block.get("data_dir")
    if not data_dir:
        return
    shutil.copytree(prepare_remote_data(config), data_dir, dirs_exist_ok=True)


HTTPFS_HTTP_SERVICE = use_service(HTTPSERVER_SERVICE, populate=httpfs_http_populate)
