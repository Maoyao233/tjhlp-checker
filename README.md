# TJHLP-CHECKER 同济高程代码合规检查

## 简介

*高级语言程序设计* 是为同济大学信息类大一学生开设的专业入门课，使用 C/C++ 教学。由于教学需求，课程对作业中允许使用的语言特性做出了一定的限制。本项目基于 [libclang](https://clang.llvm.org/doxygen/group__CINDEX.html) 的 [Python binding](https://pypi.org/project/clang/) 实现，提供 AST 级别的准确检测工具。

## 构建

本项目使用 [uv](https://docs.astral.sh/uv/) 进行项目管理。

```bash
uv sync
uv build
```

由于 Clang 的 Python binding 库并未包含 libclang 的二进制文件，因此使用者需要自行[安装 LLVM](https://releases.llvm.org/)，并在配置文件中设定 libclang.dll/libclang.so 所在的目录。

更简便的方法是直接使用 Docker:

```bash
docker build -t tjhlp-checker .
docker run -it tjhlp-checker
```

## 使用

```bash
tjhlp-checker --config-file=<PATH TO CONFIG FILE> <FILE>
```

配置文件使用 TOML 格式。具体配置项请参考 [src/tjhlp_checker/config.py]。
