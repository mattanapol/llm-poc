from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import math
def list_to_numbered_list(list_str: list):
    # numbered_lines = ""
    result = []
    for index, item in enumerate(list_str):
        # numbered_lines += f"{index}-{item}"
        result.append(f"{index}-{item}")
    return result

def list_to_lines(list_str: list):
    return "\n".join(list_str)

def numbered_lines_to_dict(input_str):
    output_dict = {}
    lines = input_str.split("\n")
    for line in lines:
        try:
            key, value = line.split("-")
        except ValueError:
            continue
        output_dict[int(key)] = value
    return output_dict

def translate(original_sentences: list, glossary_dict: dict): 
    llm = ChatOpenAI(model="gpt-4o")

    prompt = ChatPromptTemplate.from_messages([
        ("system",
        """
        You are movie subtitle translator that can translate Chinese into Thai.
        You will be provide with list of original Chinese subtitle string.
        You have to translate each of them and while keep same number of sentence.
        This will be list of glossary that you can use to help you translate.
        {glossary}
        Output should be in line, while the number of line should be the same as number of sentence.
        Example input:
        ```
        0-[离婚协议书]
        1-[未完待续]
        2-你来这干嘛啊
        3-怎么
        4-我来的不是时候了
        5-打扰我老公
        6-跟我闺蜜的好事了
        7-还有你陈雅舒
        8-我把你当亲姐妹
        9-你居然
        ```
        Example output:
        ```
        0-[สัญญาหย่า]
        1-[ติดตามตอนต่อไป]
        2-มาทำไมเนี่ย
        3-ทำไม
        4-ฉันมารบกวน
        5-สามีฉัน
        6-กับเพื่อนซี้ฉันหรือไง
        7-ริษา
        8-เราสนิทกันขนาดนี้
        9-แต่เธอ
        ```
        """),
        ("user",
        """
        {sentences}
        """),
    ])

    output_parser = StrOutputParser()

    chain = prompt | llm | output_parser
    page_size = 35
    output_dict = {}
    numbered_sentences = list_to_numbered_list(original_sentences)
    for i in range(math.ceil(len(original_sentences)/page_size)):
        input_sentences = "\n".join(numbered_sentences[i*page_size:max((i+1)*page_size, len(original_sentences))])
        output = chain.invoke({"sentences": input_sentences, "glossary": glossary_dict})
        output_dict.update(numbered_lines_to_dict(output))
    return output_dict