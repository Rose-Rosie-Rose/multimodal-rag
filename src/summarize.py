# 저장한 데이터를 불러와 요약하고 저장

import base64
import pickle
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

load_dotenv(PROJECT_ROOT / ".env")

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# 텍스트와 표 요약
def generate_text_summaries(texts, tables, summarize_texts=False):
    prompt = ChatPromptTemplate.from_template(
        "다음 텍스트나 표를 검색에 적합하도록 간결하게 요약하세요. "
        "핵심 키워드와 중요한 수치를 포함하고 한국어로 작성하세요.\n"
        "{element}"
    )

    chain = prompt | model | StrOutputParser()

    text_summaries = texts
    if texts and summarize_texts:
        text_summaries = chain.batch(
            [{"element": text} for text in texts],
            config={"max_concurrency": 5},
        )

    table_summaries = []
    if tables:
        table_summaries = chain.batch(
            [{"element": table} for table in tables],
            config={"max_concurrency": 1},
        )

    return text_summaries, table_summaries


# 이미지 파일을 Base64 문자열로 변환
def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# 이미지 요약
def image_summarize(img_base64, prompt, mime_type="image/jpeg"):
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{img_base64}"
                },
            },
        ]
    )
    return (model | StrOutputParser()).invoke([message])


def generate_img_summaries(path):
    img_base64_list = []
    image_summaries = []

    prompt = (
        "이 이미지를 검색에 적합하도록 한국어로 간결하게 요약하세요. "
        "그래프나 표라면 제목, 항목, 중요한 수치와 추세를 포함하세요."
    )

    for image_path in sorted(Path(path).iterdir()):
        if image_path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue

        img_base64 = encode_image(image_path)
        mime_type = (
            "image/png"
            if image_path.suffix.lower() == ".png"
            else "image/jpeg"
        )
        summary = image_summarize(img_base64, prompt, mime_type)

        img_base64_list.append(img_base64)
        image_summaries.append(summary)
        print("이미지 요약 완료:", image_path.name)

    return img_base64_list, image_summaries


if __name__ == "__main__":
    # 추출 결과 불러오기
    output_dir = DATA_DIR / "processed"

    with open(output_dir / "extracted.pkl", "rb") as f:
        data = pickle.load(f)

    text_summaries, table_summaries = generate_text_summaries(
        data["texts_2k_token"],
        data["tables"],
        summarize_texts=True,
    )
    print("텍스트·표 요약 완료")

    img_base64_list, image_summaries = generate_img_summaries(
        DATA_DIR / "figures"
    )

    # 요약 결과 저장
    with open(output_dir / "summaries.pkl", "wb") as f:
        pickle.dump(
            {
                "text_summaries": text_summaries,
                "table_summaries": table_summaries,
                "image_summaries": image_summaries,
                "img_base64_list": img_base64_list,
            },
            f,
        )

    print(f"텍스트 요약: {len(text_summaries)}개")
    print(f"표 요약: {len(table_summaries)}개")
    print(f"이미지 요약: {len(image_summaries)}개")
    print("저장 완료:", output_dir / "summaries.pkl")