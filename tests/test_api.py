from openai import OpenAI

from config.settings import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_MODEL
)

def test_api_connection():
    client = OpenAI(
        api_key=AI_API_KEY,
        base_url=AI_BASE_URL,
        timeout=60
    )

    response = client.chat.completions.create(

        model=AI_MODEL,

        messages=[
            {
                "role": "user",
                "content": "你好，请回复：API测试成功"
            }
        ],

        temperature=0
    )

    result = response.choices[0].message.content

    print("\nAI返回:")
    print(result)

    assert result is not None
    assert len(result) > 0

if __name__ == "__main__":

    test_api_connection()

    print("\n✅ API测试通过")