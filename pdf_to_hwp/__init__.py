"""PDF to HWP Converter - PDF 파일을 이미지화하여 HWP로 변환하는 에이전트"""

__version__ = "1.0.0"
__author__ = "Jingyeskan"

from .converter import PDFConverter
from .hwp_generator import HWPGenerator
from .agent import PDFToHWPAgent, convert_pdf_to_hwp

__all__ = [
    "PDFConverter",
    "HWPGenerator",
    "PDFToHWPAgent",
    "convert_pdf_to_hwp",
    "merge_pdfs_to_hwp",
]


def merge_pdfs_to_hwp(
    pdf_paths: list,
    output_path: str,
    dpi: int = 300,
    show_progress: bool = True,
) -> str:
    """
    여러 PDF 파일을 하나의 HWP로 병합하는 간편 함수

    Args:
        pdf_paths: PDF 파일 경로 리스트 (순서대로 병합됨)
        output_path: 출력 HWP 파일 경로
        dpi: 이미지 해상도 (기본값: 300)
        show_progress: 진행 상황 표시 여부

    Returns:
        생성된 HWP 파일 경로
    """
    with PDFToHWPAgent(dpi=dpi) as agent:
        return agent.merge_pdfs(pdf_paths, output_path, show_progress)
