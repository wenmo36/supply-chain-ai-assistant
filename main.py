from ai.model import ask



def main():


    print("==============================")

    print("供应链 AI 数据分析助手 V1.1")

    print("输入 exit 退出")

    print("==============================")


    while True:


        question=input("\n你：").strip()


        if question.lower() in [
            "exit",
            "quit",
            "退出"
        ]:

            break


        try:

            result=ask(question)


            print(
                "\n--- AI分析 ---"
            )

            print(result)


        except Exception as e:

            print(
                "\n错误:",
                e
            )



if __name__=="__main__":

    main()