
from typing import Union, List, Any, Dict, Generator, Iterable
from hashlib import sha256
from functools import reduce

def dict_to_sha256_hex_digest(_dict):
    
    """Converts dictionary to sha256 hex digest.

    Sensitive to changes in presence and string value of any k/v pairs.
    """
    if not _dict and not isinstance(_dict, dict):
        raise ValueError("Arg should be a non-empty dictionary")

    # order dict k/v pairs & concat their values as strings
    value_string = reduce(
        lambda t1, t2: "".join(map(str, (t1, t2))),
        sorted(_dict.items(), key=lambda t: str(t[0])),
        "",
    )

    return str_to_sha256_hex_digest(value_string)
    
def str_to_sha256_hex_digest(_str: str) -> str:
    """Converts string to sha256 hex digest"""
    if not _str and not isinstance(_str, str):
        raise ValueError("Arg should be a non-empty string")

    return sha256(_str.encode("utf-8")).hexdigest()
