from errors import ServiceUnavailableError
from typing import Type
from generate import TextGenerateBase
from manual import ManualReply

MODEL_LIST = {
    "gpt-3.5-turbo": ManualReply,
    "gpt-4": ManualReply,
}


def get_model_list(is_legacy) -> dict:
    all_model_list = MODEL_LIST.keys()

    if is_legacy:
        models = [
            {"id": id, "object": "engine", "owner": "user", "ready": True}
            for id in all_model_list
        ]
    else:
        models = [
            {
                "id": id,
                "object": "model",
                "owned_by": "user",
                "permission": [],
            }
            for id in all_model_list
        ]

    resp = {
        "object": "list",
        "data": models,
    }

    return resp


def get_model_generator(model_name) -> Type[TextGenerateBase]:
    try:
        generator = MODEL_LIST[model_name]
    except KeyError:
        raise ServiceUnavailableError(
            f"Model {model_name} does not exist.",
            internal_message=f"Model {model_name} does not exist.",
        )
    return generator


def get_engine(model_name) -> dict:
    return {
        "id": model_name,
        "object": "engine",
        "owner": "self",
        "ready": True,
    }


def get_model(model_name) -> dict:
    return {
        "id": model_name,
        "object": "model",
        "owned_by": "user",
        "permission": [],
    }
