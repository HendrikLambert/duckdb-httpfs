from ducktest import use_service
from ducktest.resources.mitmproxy import MITM_SERVICE, mitm_env

PROXY_USERNAME = "ducktest-proxy-user"
PROXY_PASSWORD = "ducktest-proxy-password"


def httpfs_mitm_env(block):
    env = mitm_env(block)
    host_port = block["endpoint"].removeprefix("http://")
    env.update({
        "HTTP_PROXY_PUBLIC": host_port,
        "HTTP_PROXY_PRIVATE": host_port,
        "HTTP_PROXY_PRIVATE_USERNAME": PROXY_USERNAME,
        "HTTP_PROXY_PRIVATE_PASSWORD": PROXY_PASSWORD,
    })
    return env


HTTPFS_MITM_SERVICE = use_service(MITM_SERVICE, to_env=httpfs_mitm_env)
