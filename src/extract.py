# PDF에서 텍스트, 표, 이미지를 추출하고 저장

import pickle
from pathlib import Path

from langchain_text_splitters import CharacterTextSplitter
from unstructured.partition.pdf import partition_pdf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# PDF에서 텍스트, 표, 이미지 추출
def extract_pdf_elements(path, fname):
    return partition_pdf(
        filename=str(Path(path) / fname),
        strategy="hi_res",
        extract_images_in_pdf=True,
        infer_table_structure=True,
        chunking_strategy="by_title",
        max_characters=4000,
        new_after_n_chars=3800,
        combine_text_under_n_chars=2000,
        extract_image_block_output_dir=str(Path(path) / "figures"),
    )

# 추출한 요소 텍스트와 표로 분류
def categorize_elements(raw_pdf_elements):
    texts = []
    tables = []

    for element in raw_pdf_elements:
        if element.category == "Table":
            tables.append(str(element))
        elif element.category == "CompositeElement":
            texts.append(str(element))

    return texts, tables

if __name__ == "__main__":
    raw_pdf_elements = extract_pdf_elements(DATA_DIR, "document.pdf")
    texts, tables = categorize_elements(raw_pdf_elements)

    # 텍스트를 토큰 기준으로 분할
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=2000,
        chunk_overlap=200,
    )
    texts_2k_token = text_splitter.split_text(" ".join(texts))

    # 요약 단계에서 사용할 데이터 저장
    output_dir = DATA_DIR / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "extracted.pkl", "wb") as f:
        pickle.dump(
            {
                "texts": texts,
                "tables": tables,
                "texts_2k_token": texts_2k_token,
            },
            f,
        )

    print(f"텍스트: {len(texts)}개")
    print(f"표: {len(tables)}개")
    print(f"분할한 텍스트: {len(texts_2k_token)}개")
    print("저장 완료:", output_dir / "extracted.pkl")