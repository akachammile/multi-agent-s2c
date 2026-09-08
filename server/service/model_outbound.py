"""模型请求仅访问已解析并校验的公网 HTTPS 地址。"""

import asyncio
import ipaddress
import socket

import httpx


class UnsafeModelTarget(ValueError):
    pass


def is_public_address(value: str) -> bool:
    address = ipaddress.ip_address(value)
    if not address.is_global or address.is_multicast or address.is_reserved or address.is_unspecified:
        return False
    if isinstance(address, ipaddress.IPv6Address):
        # 拒绝可封装 IPv4 地址的转换网段，避免绕过私网校验。
        return not any(address in ipaddress.ip_network(network) for network in (
            "::ffff:0:0/96", "64:ff9b::/96", "64:ff9b:1::/48", "2002::/16", "2001::/32",
        ))
    return True


async def resolve_public_target(base_url: str) -> tuple[httpx.URL, str, str]:
    url = httpx.URL(base_url)
    host = url.host
    if url.scheme != "https" or not host or url.username or url.password or url.query or url.fragment or "%" in host:
        raise UnsafeModelTarget("模型地址必须为公网 HTTPS 地址")
    if host.lower().rstrip(".") == "localhost" or host.lower().rstrip(".").endswith((".localhost", ".local", ".internal", ".home.arpa")):
        raise UnsafeModelTarget("禁止访问内部模型地址")
    try:
        ipaddress.ip_address(host)
        addresses = [host]
    except ValueError:
        if "." not in host:
            raise UnsafeModelTarget("禁止访问内部模型地址") from None
        records = await asyncio.wait_for(
            asyncio.get_running_loop().getaddrinfo(host, url.port or 443, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM),
            timeout=5,
        )
        addresses = list(dict.fromkeys(record[4][0] for record in records))
    if not addresses or not all(is_public_address(address) for address in addresses):
        raise UnsafeModelTarget("禁止访问内部模型地址")
    # 连接直接使用通过校验的 IP；Host / TLS SNI 保留原域名，避免二次 DNS 解析。
    authority = url.netloc.decode("ascii")
    return url.copy_with(host=addresses[0]), authority, host
