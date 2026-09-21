from openai import OpenAI
import pytest

from config.settings import (
    AI_API_KEY,
    AI_BASE_URL
)

pytestmark = pytest.mark.paid_api


def test_list_models():
    client = OpenAI(

        api_key=AI_API_KEY,

        base_url=AI_BASE_URL,

        timeout=60
    )

    models = client.models.list()

    assert models.data is not None

    print("\n当前可用模型:")

    for model in models.data:

        print(
            model.id
        )

if __name__ == "__main__":

    test_list_models()

    print("\n✅ 模型列表获取成功")
