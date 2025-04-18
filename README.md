# TJHLP-CHECKER 同济高程代码合规检查

## 简介

*高级语言程序设计* 是为同济大学信息类大一学生开设的专业入门课，使用 C/C++ 教学。由于教学需求，课程对作业中允许使用的语言特性做出了一定的限制。本项目基于 [libclang](https://clang.llvm.org/doxygen/group__CINDEX.html) 的 [Python binding](https://pypi.org/project/clang/) 实现，提供 AST 级别的准确检测工具。

## 使用

`tjhlp-checker`既可以用库的形式引入，也可以直接作为 CLI 工具使用。

### 安装

```bash
pip install tjhlp-checker
# 若需直接在命令行使用，则改为：
# pip install tjhlp-checker[cli]
```

由于 Clang 的 Python binding 库并未包含 libclang 的二进制文件，因此使用者需要自行[安装 LLVM](https://releases.llvm.org/)，并正确设置环境变量 `LIBCLANG_PATH` 为 libclang.dll/libclang.so 所在的目录。

如果这个过程存在困难，或者不希望引入这么重的依赖，也可以直接使用 Docker。

### 作为库引入

```Python
import sys

from tjhlp-checker import load_config, find_all_violations

if __name__ == '__main__':
    """
    Usage: python main.py <cpp file> <config file>
    """
    with open(sys.argv[2], 'rb') as conf:
        violations = find_all_violations(
            sys.argv[1],
            load_config(conf)
        )
    print(violations)
```

### 直接在命令行使用

```bash
pip install tjhlp-checker[cli]
tjhlp-checker --config-file=<PATH TO CONFIG FILE> <FILE>
```

配置文件使用 TOML 格式。由于本项目使用 [Pydantic](https://docs.pydantic.dev/latest/) 验证配置文件格式，因此具体配置项可以直接参考 [src/tjhlp_checker/config.py](src/tjhlp_checker/config.py)。

## 构建

本项目使用 [uv](https://docs.astral.sh/uv/) 进行项目管理。

```bash
git clone https://github.com/Maoyao233/tjhlp-checker && cd tjhlp-checker
uv sync
uv build
```

### 使用 Docker

更简便的方法是直接使用 Docker:

```bash
docker build -t tjhlp-checker .
docker run -it tjhlp-checker
```
