### 폴더 구조
```
multimodal-rag/
├── .venv/                      # 가상환경 (Git 제외)
├── .env                        # API 키 (Git 제외, 절대 커밋 금지)
├── .env.example                # 키 없는 템플릿 (Git 포함)
├── .gitignore
├── requirements.txt            # 의존성 목록
├── requirements.lock.txt       # 버전 고정 파일
├── README.md                   # 포트폴리오의 얼굴
├── data/
│   ├── invest.pdf              # 원본 PDF
│   └── figures/                # 추출된 이미지 (Git 제외, 용량 큼)
├── notebooks/
│   └── Multi_modal_RAG.ipynb   # 실습 노트북
└── src/
    ├── extract.py              # PDF 파싱 함수
    ├── summarize.py            # 요약 체인
    └── retriever.py            # 다중 벡터 검색기
```

### 실행 방법

git clone <저장소 주소>
cd multimodal-rag

#### 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate          # 윈도우: .venv\Scripts\activate

#### 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt     # 또는 requirements.lock.txt

#### 커널 등록
python -m ipykernel install --user --name multimodal-rag

#### .env 작성
cp .env.example .env                # 윈도우: copy .env.example .env
#### .env 파일을 열어 실제 API 키를 입력


### 트러블 슈팅
| 증상 | 원인 | 해결 |
| --- | --- | --- |
| `(.venv)` 표시가 안 보임 | 활성화 안 됨 | 운영체제별 활성화 명령 재실행 |
| PowerShell에서 활성화 거부 | 실행 정책 제한 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `ModuleNotFoundError` | 활성화 없이 설치했거나 커널이 다름 | `(.venv)` 확인 후 재설치, 노트북 커널 재선택 |
| VS Code에서 커널이 안 보임 | 인터프리터 미지정 | `Ctrl+Shift+P` → `Python: Select Interpreter` → `.venv` 선택 |
| `pip` 설치 중 멈춤 | 구버전 pip | `python -m pip install --upgrade pip` 후 재시도 |
| `PDFInfoNotInstalledError` | Poppler 미설치 / Path 누락 | OS 패키지 설치 후 **터미널·에디터 완전 재시작** |
| `TesseractNotFoundError` | Tesseract Path 누락 | `C:\Program Files\Tesseract-OCR` 추가 후 재시작 |
| `unstructured` 설치가 매우 느림 | `all-docs`가 대용량 의존성 포함 | 정상. 5~15분 소요. 중단하지 말 것 |
| 윈도우에서 파싱 시 경로 오류 | 경로에 한글·공백 포함 | `C:\dev\multimodal-rag` 같은 경로로 이동 |
| 설치는 됐는데 import 실패 | 파이썬 버전 불일치 | `python --version`이 3.11/3.12인지 확인 |