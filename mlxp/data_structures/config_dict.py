"""A dictionary-like structure for storing the configurations."""

from typing import Any, Dict, Type

import omegaconf
import yaml


class ConfigDict(dict):
    """A subclass of the dict class containing the configuration options.

    The value corresponding to a key can be accessed as an attribute: self.key
    """

    def __init__(self, *args, **kwargs):
        super(ConfigDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def __repr__(self):
        """Define custom string representation for ConfigDict objects."""
        return f"{yaml.dump(convert_dict(self,src_class=ConfigDict,dst_class=dict))}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object into a simple dictionary.

        :return: A dictionary containing the same information as self
        :rtype: Dict[str,Any]
        """
        return convert_dict(self, src_class=ConfigDict, dst_class=dict)

    def update(self, new_dict: Dict[str, Any]) -> None:
        """Update the dictionary based on an input dictionary-like object.

        :param new_dict: Dictionary-like object.
        :type new_dict: Dict[str, Any]
        """
        new_dict = convert_dict(new_dict, src_class=dict)
        for key, value in new_dict.items():
            if key in self.keys():
                if isinstance(value, dict):
                    if isinstance(self[key], ConfigDict):
                        self[key].update(value)
                    else:
                        self[key] = convert_dict(value, src_class=dict)
                else:
                    self[key] = value
            else:
                if isinstance(value, dict):
                    self[key] = convert_dict(value, src_class=dict)
                else:
                    self[key] = value


def convert_dict(
    src_dict: Any, src_class: Type = omegaconf.dictconfig.DictConfig, dst_class: Type = ConfigDict,
) -> Any:
    """Convert a dictionary-like object from a source class to a destination dictionary-
    like object of a destination class.

    :param src_dict: The source dictionary to be converted
    :param src_class: The type of the src dictionary
    :param dst_class: The destination type of the returned dictionary-like object.
    :type src_dict: Any
    :type src_class: Type
    :type dst_class: Type
    :return: A dictionary-like instance of the dst_class copying the data from the
        src_dict.
    :rtype: Any
    """
    dst_dict = {}
    for key, value in src_dict.items():
        if isinstance(value, src_class):
            dst_dict[key] = convert_dict(value, src_class=src_class, dst_class=dst_class)
        else:
            if isinstance(value, omegaconf.listconfig.ListConfig):
                value = list(value)
            dst_dict[key] = value
    dst_dict = dst_class(dst_dict)
    return dst_dict
