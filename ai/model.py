import json

from openai import OpenAI


from config.settings import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_MODEL,
    AI_TIMEOUT_SECONDS,
    AI_MAX_RETRIES
)


from ai.prompt import SYSTEM_PROMPT


from database.query import run_readonly_sql



client=OpenAI(

    api_key=AI_API_KEY,

    base_url=AI_BASE_URL,

    timeout=AI_TIMEOUT_SECONDS,

    max_retries=AI_MAX_RETRIES

)



TOOLS=[

{
"type":"function",

"function":{

"name":"run_readonly_sql",

"description":
"执行供应链数据库只读SQL查询",

"parameters":{

"type":"object",

"properties":{

"sql":{

"type":"string"

}

},

"required":[
"sql"
]

}

}

}

]




def ask(question):


    messages=[

    {
    "role":"system",
    "content":SYSTEM_PROMPT
    },

    {
    "role":"user",
    "content":question
    }

    ]



    response=client.chat.completions.create(

        model=AI_MODEL,

        messages=messages,

        tools=TOOLS,

        tool_choice="auto",

        temperature=0

    )


    assistant=response.choices[0].message


    messages.append(assistant)



    if not assistant.tool_calls:

        return assistant.content



    for call in assistant.tool_calls:


        args=json.loads(
            call.function.arguments
        )


        sql=args["sql"]


        print("\n--- SQL ---")

        print(sql)



        rows=run_readonly_sql(sql)



        messages.append(

        {

        "role":"tool",

        "tool_call_id":call.id,

        "content":json.dumps(

            {
            "rows":rows[:200]
            },

            ensure_ascii=False,

            default=str

        )

        }

        )


    final=client.chat.completions.create(

        model=AI_MODEL,

        messages=messages,

        temperature=0.2

    )


    return final.choices[0].message.content
