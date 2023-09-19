## 手动 OpenAI API 服务器 Manual API Server for OpenAI API

一个兼容 OpenAI API 的服务端，但是允许用户手动输入回复。

A OpenAI API compatible server, but allows user to input reply manually.

### 使用方法 Usage

使用 Python 3 直接运行 `main.py`。无需安装任何依赖。

Run `main.py` with Python 3. No dependencies required.

```bash
python main.py
```

### 扩展 Extension

你可以查看 `generate.py`, 实现 TextGenerateBase 中的各个方法的类即可作为扩展。修改 `models.py` 中的 `MODEL_LIST` 常量，将你的模型名以及对应类加入到字典中即可。

You can check `generate.py`, implement a class that implements all methods in TextGenerateBase. Modify `MODEL_LIST` in `models.py`, add your model name and class to the dictionary.

### 参考 Reference

本项目参考了 [text-generation-webui](https://github.com/oobabooga/text-generation-webui/) 中 OpenAI API 服务端的实现。

This project refers to the implementation of OpenAI API server in [text-generation-webui](https://github.com/oobabooga/text-generation-webui/)