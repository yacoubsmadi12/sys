from app.parsers.base import BaseParser
from app.parsers.huawei import HuaweiParser
from app.parsers.nokia import NokiaParser
from app.parsers.ericsson import EricssonParser

VENDOR_PARSERS: dict[str, BaseParser] = {
    "huawei": HuaweiParser(),
    "nokia": NokiaParser(),
    "ericsson": EricssonParser(),
}


def get_parser(vendor: str) -> BaseParser | None:
    return VENDOR_PARSERS.get(vendor.lower())
