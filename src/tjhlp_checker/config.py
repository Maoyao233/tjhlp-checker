import tomllib
from typing import Self
from pydantic import BaseModel, model_validator
from typing import BinaryIO
import codecs


class CommonConfig(BaseModel):
    encoding: str = "utf-8"

    @model_validator(mode="after")
    def verify(self) -> Self:
        try:
            codecs.lookup(self.encoding)
        except LookupError:
            raise ValueError(f"{self.encoding} is not a valid encoding")
        return self


class HeaderConfig(BaseModel):
    blacklist: list[str] = []
    whitelist: list[str] = []

    @model_validator(mode="after")
    def verify(self) -> Self:
        if self.blacklist and self.whitelist:
            raise ValueError("blacklist and whitelist cannot both be set")
        return self


class GrammarConfig(BaseModel):
    disable_int64_or_larger: bool = False
    disable_pointers: bool = False
    disable_reference: bool = False
    disable_array: bool = False
    disable_struct: bool = False
    disable_class: bool = False
    disable_function: bool = False
    disable_branch: bool = False
    disable_goto: bool = False
    disable_loop: bool = False
    disable_bit_operation: bool = False
    disable_external_global_var: bool = False
    disable_internal_global_var: bool = False  # static global/in anonymous namespace
    disable_static_local_var: bool = False

    class SystemClassConfig(BaseModel):
        disable: bool = False
        whitelist: list[str] = []

    system_class: SystemClassConfig = SystemClassConfig()


class Config(BaseModel):
    common: CommonConfig = CommonConfig()
    header: HeaderConfig = HeaderConfig()
    grammar: GrammarConfig = GrammarConfig()


def load_config(file: BinaryIO):
    return Config.model_validate(tomllib.load(file))
