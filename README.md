# PDF to HWP Converter

PDF 파일을 이미지화하여 HWP(한글 워드프로세서) 파일로 변환하는 Python 에이전트입니다.

## 기능

- PDF의 각 페이지를 고해상도 이미지로 변환
- 변환된 이미지를 HWP 문서에 페이지별로 삽입
- 일괄 변환 지원 (여러 PDF 파일 동시 처리)
- CLI 및 Python API 지원
- 진행 상황 실시간 표시

## 설치

### 1. 저장소 클론

```bash
git clone https://github.com/eunseok7979/Jingyeskan-1.0.git
cd Jingyeskan-1.0
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. (선택) 패키지 설치

```bash
pip install -e .
```

## 시스템 요구사항

- Python 3.8 이상
- pyhwpx 사용 시: Windows + 한컴오피스 설치 필요
- pyhwpx 없이도 HWPX 포맷으로 출력 가능 (모든 OS 지원)

## 사용법

### CLI 사용

#### 단일 파일 변환

```bash
# 기본 사용법
python main.py convert document.pdf

# 출력 파일 지정
python main.py convert document.pdf -o output.hwp

# 해상도 조정 (기본값: 300 DPI)
python main.py convert document.pdf -d 150

# 페이지 크기 및 여백 조정
python main.py convert document.pdf --page-width 210 --page-height 297 --margin 5

# 조용한 모드 (진행 상황 미표시)
python main.py convert document.pdf -q
```

#### 일괄 변환

```bash
# 여러 파일 변환
python main.py batch doc1.pdf doc2.pdf doc3.pdf

# 출력 디렉토리 지정
python main.py batch *.pdf -o ./converted/
```

#### PDF 정보 확인

```bash
python main.py info document.pdf
```

### Python API 사용

#### 간단한 사용

```python
from pdf_to_hwp import convert_pdf_to_hwp

# 단일 파일 변환
hwp_path = convert_pdf_to_hwp("document.pdf")
print(f"변환 완료: {hwp_path}")
```

#### 에이전트 사용

```python
from pdf_to_hwp import PDFToHWPAgent

# 에이전트 생성
agent = PDFToHWPAgent(
    dpi=300,           # 이미지 해상도
    page_width=210.0,  # A4 너비 (mm)
    page_height=297.0, # A4 높이 (mm)
    margin=10.0,       # 여백 (mm)
)

# Context manager 사용 (자동 리소스 정리)
with agent:
    # 단일 파일 변환
    result = agent.convert("document.pdf", "output.hwp")

    # 일괄 변환
    results = agent.convert_batch(
        ["doc1.pdf", "doc2.pdf"],
        output_dir="./output/"
    )
```

#### 진행 상황 콜백

```python
from pdf_to_hwp import PDFToHWPAgent

def on_progress(current, total, message):
    print(f"[{current}/{total}] {message}")

agent = PDFToHWPAgent()
agent.set_progress_callback(on_progress)

with agent:
    agent.convert("document.pdf")
```

#### 개별 모듈 사용

```python
from pdf_to_hwp import PDFConverter, HWPGenerator

# PDF를 이미지로만 변환
converter = PDFConverter(dpi=300)
images = converter.convert_all_pages("document.pdf", output_dir="./images/")

# 이미지를 HWP로 변환
generator = HWPGenerator()
image_paths = ["page1.png", "page2.png", "page3.png"]
generator.create_hwp_from_images(image_paths, "output.hwp")
```

## 프로젝트 구조

```
Jingyeskan-1.0/
├── pdf_to_hwp/
│   ├── __init__.py        # 패키지 초기화 및 exports
│   ├── converter.py       # PDF → 이미지 변환
│   ├── hwp_generator.py   # 이미지 → HWP 변환
│   └── agent.py           # 메인 에이전트 로직
├── main.py                # CLI 인터페이스
├── requirements.txt       # 의존성 목록
├── setup.py               # 패키지 설치 설정
└── README.md              # 이 파일
```

## HWP 출력 형식

### pyhwpx 사용 가능한 경우 (Windows + 한컴오피스)
- 네이티브 HWP 파일 생성
- 완벽한 호환성

### pyhwpx 사용 불가능한 경우 (Linux/Mac 또는 한컴오피스 미설치)
- HWPX 포맷으로 출력 (.hwpx)
- HWPX는 한글 2014 이상에서 지원하는 개방형 문서 포맷
- 한컴오피스나 한글 뷰어에서 열기 가능

## 옵션 설명

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--dpi`, `-d` | 300 | 이미지 변환 해상도. 높을수록 품질이 좋지만 파일 크기 증가 |
| `--page-width` | 210.0 | HWP 페이지 너비 (mm). A4 기준 |
| `--page-height` | 297.0 | HWP 페이지 높이 (mm). A4 기준 |
| `--margin` | 10.0 | 페이지 여백 (mm) |
| `--quiet`, `-q` | False | 진행 상황 표시 끄기 |

## 라이선스

MIT License

## 기여

이슈와 풀 리퀘스트를 환영합니다!
