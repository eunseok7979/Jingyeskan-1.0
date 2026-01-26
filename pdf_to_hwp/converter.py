"""PDF를 이미지로 변환하는 모듈"""

import os
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

import fitz  # PyMuPDF
from PIL import Image
from tqdm import tqdm


class PDFConverter:
    """PDF 파일을 페이지별 이미지로 변환하는 클래스"""

    def __init__(self, dpi: int = 300, image_format: str = "PNG"):
        """
        PDFConverter 초기화

        Args:
            dpi: 출력 이미지의 해상도 (기본값: 300)
            image_format: 출력 이미지 포맷 (기본값: PNG)
        """
        self.dpi = dpi
        self.image_format = image_format.upper()
        self.zoom = dpi / 72  # PDF 기본 해상도는 72 DPI

    def get_page_count(self, pdf_path: str) -> int:
        """
        PDF 파일의 페이지 수를 반환

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            페이지 수
        """
        with fitz.open(pdf_path) as doc:
            return len(doc)

    def convert_page_to_image(
        self, pdf_path: str, page_number: int, output_path: Optional[str] = None
    ) -> Image.Image:
        """
        PDF의 특정 페이지를 이미지로 변환

        Args:
            pdf_path: PDF 파일 경로
            page_number: 변환할 페이지 번호 (0부터 시작)
            output_path: 저장할 경로 (선택사항)

        Returns:
            PIL Image 객체
        """
        with fitz.open(pdf_path) as doc:
            page = doc.load_page(page_number)
            mat = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=mat)

            # PIL Image로 변환
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            if output_path:
                img.save(output_path, self.image_format)

            return img

    def convert_all_pages(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None,
        show_progress: bool = True,
    ) -> List[Tuple[int, Image.Image, Optional[str]]]:
        """
        PDF의 모든 페이지를 이미지로 변환

        Args:
            pdf_path: PDF 파일 경로
            output_dir: 이미지 저장 디렉토리 (선택사항)
            show_progress: 진행 상황 표시 여부

        Returns:
            (페이지 번호, Image 객체, 저장 경로) 튜플 리스트
        """
        results = []
        page_count = self.get_page_count(pdf_path)

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        pdf_name = Path(pdf_path).stem
        pages = range(page_count)

        if show_progress:
            pages = tqdm(pages, desc="PDF 페이지 변환 중", unit="page")

        for page_num in pages:
            output_path = None
            if output_dir:
                ext = self.image_format.lower()
                output_path = os.path.join(
                    output_dir, f"{pdf_name}_page_{page_num + 1:04d}.{ext}"
                )

            img = self.convert_page_to_image(pdf_path, page_num, output_path)
            results.append((page_num, img, output_path))

        return results

    def convert_to_temp_images(
        self, pdf_path: str, show_progress: bool = True
    ) -> List[Tuple[int, str]]:
        """
        PDF를 임시 디렉토리에 이미지로 변환

        Args:
            pdf_path: PDF 파일 경로
            show_progress: 진행 상황 표시 여부

        Returns:
            (페이지 번호, 임시 파일 경로) 튜플 리스트
        """
        temp_dir = tempfile.mkdtemp(prefix="pdf_to_hwp_")
        results = self.convert_all_pages(pdf_path, temp_dir, show_progress)
        return [(page_num, path) for page_num, _, path in results]


def convert_pdf_to_images(
    pdf_path: str,
    output_dir: Optional[str] = None,
    dpi: int = 300,
    show_progress: bool = True,
) -> List[str]:
    """
    PDF 파일을 이미지로 변환하는 간편 함수

    Args:
        pdf_path: PDF 파일 경로
        output_dir: 출력 디렉토리 (기본값: PDF와 같은 디렉토리)
        dpi: 이미지 해상도
        show_progress: 진행 상황 표시 여부

    Returns:
        생성된 이미지 파일 경로 리스트
    """
    if output_dir is None:
        output_dir = Path(pdf_path).parent / f"{Path(pdf_path).stem}_images"

    converter = PDFConverter(dpi=dpi)
    results = converter.convert_all_pages(pdf_path, str(output_dir), show_progress)

    return [path for _, _, path in results if path]
