from models import get_model_generator
import time


def stream_chat_completions(body: dict, is_legacy: bool = False):
    # Chat Completions
    stream_object_type = "chat.completions.chunk"
    created_time = int(time.time())
    cmpl_id = "chatcmpl-%d" % (int(time.time() * 1000000000))
    resp_list = "data" if is_legacy else "choices"
    model = body.get("model")

    def chat_streaming_chunk(content):
        # begin streaming
        chunk = {
            "id": cmpl_id,
            "object": stream_object_type,
            "created": created_time,
            "model": model,
            resp_list: [
                {
                    "index": 0,
                    "finish_reason": None,
                    # So yeah... do both methods? delta and messages.
                    "message": {"role": "assistant", "content": content},
                    "delta": {"role": "assistant", "content": content},
                }
            ],
        }
        return chunk

    yield chat_streaming_chunk("")

    generator = get_model_generator(model)(body)

    for new_content in generator.stream_generate():
        chunk = chat_streaming_chunk(new_content)
        yield chunk
    chunk = chat_streaming_chunk("")
    chunk[resp_list][0]["finish_reason"] = "stop"
    chunk["usage"] = generator.token_count()
    yield chunk


def chat_completions(body: dict, is_legacy: bool = False) -> dict:
    object_type = "chat.completions"
    created_time = int(time.time())
    cmpl_id = "chatcmpl-%d" % (int(time.time() * 1000000000))
    resp_list = "data" if is_legacy else "choices"
    model = body.get("model")

    generator = get_model_generator(model)(body)

    completion = generator.generate()
    usage = generator.token_count()
    resp = {
        "id": cmpl_id,
        "object": object_type,
        "created": created_time,
        "model": model,
        resp_list: [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": completion},
            }
        ],
        "usage": usage,
    }
    return resp
