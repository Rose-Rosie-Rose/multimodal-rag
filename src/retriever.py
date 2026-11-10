# 요약으로 원본을 검색하고, 질문에 답하는 최종 체인 연결
import pickle
import uuid
from pathlib import Path

import langchain_classic.retrievers.multi_vector
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.stores import InMemoryStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


# 요약과 원본을 같은 ID로 연결
def add_documents(retriever, summaries, contents, kind):
    if len(summaries) != len(contents):
        raise ValueError("요약과 원본 개수가 다릅니다.")

    if not summaries:
        return

    ids = [str(uuid.uuid4()) for _ in contents]

    summary_docs = [
        Document(page_content=summary, metadata={"doc_id": doc_id})
        for doc_id, summary in zip(ids, summaries)
    ]
    original_docs = [
        Document(page_content=content, metadata={"kind": kind})
        for content in contents
    ]

    retriever.vectorstore.add_documents(summary_docs)
    retriever.docstore.mset(list(zip(ids, original_docs)))


# 검색된 원본을 텍스트와 이미지로 분리
def split_image_text_types(docs):
    return {
        "images": [
            doc.page_content
            for doc in docs if doc.metadata["kind"] == "image"
        ],
        "texts": [
            doc.page_content
            for doc in docs if doc.metadata["kind"] != "image"
        ],
    }


# 원본 자료와 질문을 모델에 전달
def img_prompt_func(data):
    content = []

    for image in data["context"]["images"]:
        mime = "image/png" if image.startswith("iVBORw0KGgo") else "image/jpeg"
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{image}"},
        })

    texts = "\n\n".join(data["context"]["texts"])
    content.append({
        "type": "text",
        "text": (
            "제공된 자료를 근거로 질문에 한국어로 답하세요.\n"
            "자료에 없는 내용은 모른다고 답하세요.\n\n"
            f"질문: {data['question']}\n\n참고 자료:\n{texts}"
        ),
    })

    return [HumanMessage(content=content)]


if __name__ == "__main__":
    # 추출 결과와 요약 결과 불러오기
    output_dir = PROJECT_ROOT / "data" / "processed"

    with open(output_dir / "extracted.pkl", "rb") as f:
        extracted = pickle.load(f)

    with open(output_dir / "summaries.pkl", "rb") as f:
        summaries = pickle.load(f)

    # 검색기 생성
    vectorstore = Chroma(
        collection_name="multimodal_rag",
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
    )

    retriever = langchain_classic.retrievers.multi_vector.MultiVectorRetriever(
        vectorstore=vectorstore,
        docstore=InMemoryStore(),
        id_key="doc_id",
        search_kwargs={"k": 4},
    )

    add_documents(
        retriever,
        summaries["text_summaries"],
        extracted["texts_2k_token"],
        "text",
    )
    add_documents(
        retriever,
        summaries["table_summaries"],
        extracted["tables"],
        "table",
    )
    add_documents(
        retriever,
        summaries["image_summaries"],
        summaries["img_base64_list"],
        "image",
    )
    print("검색기 준비 완료")

    # 검색 → 원본 분리 → 프롬프트 → 답변
    chain = (
        {
            "context": retriever | RunnableLambda(split_image_text_types),
            "question": RunnablePassthrough(),
        }
        | RunnableLambda(img_prompt_func)
        | ChatOpenAI(model="gpt-4o-mini", temperature=0)
        | StrOutputParser()
    )

    question = (
        "20페이지의 표 1 '노인 낙상으로 인한 심각한 외상성 뇌손상 "
        "환자의 세부 낙상 기전'을 기준으로, "
        "평평한 곳에서 미끄러지거나 걸려 넘어짐, 계단에서 낙상, "
        "계단 외 장소에서 낙상의 실내·실외 환자 수와 비율을 "
        "각각 표로 비교해 주세요. "
        "실내와 실외 각각에서 가장 높은 비율을 차지하는 유형도 알려주세요."
    )
    print("질문:", question)
    print(chain.invoke(question))