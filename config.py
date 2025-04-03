import tomllib
from typing import Self
from pydantic import BaseModel, model_validator
from typing import BinaryIO
from pathlib import Path

class CommonConfig(BaseModel):
    libclang_path: Path | None = None
    libclang_file: Path | None = None

    @model_validator(mode="after")
    def verify(self) -> Self:
        if not self.libclang_path and not self.libclang_file:
            raise ValueError("must set libclang_path or libclang_file")
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
    disable_auto: bool = False
    disable_branch: bool = False
    disable_goto: bool = False
    disable_loop: bool = False
    disable_range_based_loop: bool = False
    disable_bit_operation: bool = False

    class SystemClassConfig(BaseModel):
        disable: bool = False
        whitelist: list[str] = []
    
    system_class: SystemClassConfig = SystemClassConfig()


class Config(BaseModel):
    common: CommonConfig
    header: HeaderConfig = HeaderConfig()
    grammar: GrammarConfig = GrammarConfig()
    debug: bool = False


def load_config(file: BinaryIO):
    return Config.model_validate(tomllib.load(file))
