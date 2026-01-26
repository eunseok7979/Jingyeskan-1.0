"""PDF to HWP 변환 에이전트"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Callable

from .converter import PDFConverter
from .hwp_generator import HWPGenerator


class PDFToHWPAgent:
    """
    PDF 파일을 HWP로 변환하는 에이전트

    PDF의 각 페이지를 이미지로 변환한 후 HWP 문서에 삽입합니다.
    """

    def __init__(
        self,
        dpi: int = 300,
        page_width: float = 210.0,
        page_height: float = 297.0,
        margin: float = 10.0,
        keep_temp_files: bool = False,
    ):
        """
        PDFToHWPAgent 초기화

        Args:
            dpi: 이미지 변환 해상도 (기본값: 300)
            page_width: HWP 페이지 너비 mm (기본값: A4 210mm)
            page_height: HWP 페이지 높이 mm (기본값: A4 297mm)
            margin: 페이지 여백 mm (기본값: 10mm)
            keep_temp_files: 임시 파일 유지 여부 (기본값: False)
        """
        self.dpi = dpi
        self.page_width = page_width
        self.page_height = page_height
        self.margin = margin
        self.keep_temp_files = keep_temp_files

        self.pdf_converter = PDFConverter(dpi=dpi)
        self.hwp_generator = HWPGenerator(
            page_width=page_width,
            page_height=page_height,
            margin=margin,
        )

        self._progress_callback: Optional[Callable[[int, int, str], None]] = None
        self._temp_dirs: List[str] = []

    def set_progress_callback(
        self, callback: Callable[[int, int, str], None]
    ) -> None:
        """
        진행 상황 콜백 설정

        Args:
            callback: (현재 단계, 전체 단계, 메시지) 형태의 콜백 함수
        """
        self._progress_callback = callback

    def _report_progress(self, current: int, total: int, message: str) -> None:
        """진행 상황 보고"""
        if self._progress_callback:
            self._progress_callback(current, total, message)

    def convert(
        self,
        pdf_path: str,
        output_path: Optional[str] = None,
        show_progress: bool = True,
    ) -> str:
        """
        PDF 파일을 HWP로 변환

        Args:
            pdf_path: 입력 PDF 파일 경로
            output_path: 출력 HWP 파일 경로 (기본값: PDF와 같은 이름.hwp)
            show_progress: 진행 상황 표시 여부

        Returns:
            생성된 HWP 파일 경로
        """
        # 입력 파일 확인
        pdf_path = os.path.abspath(pdf_path)
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

        if not pdf_path.lower().endswith('.pdf'):
            raise ValueError("PDF 파일이 아닙니다.")

        # 출력 경로 설정
        if output_path is None:
            output_path = pdf_path.rsplit('.', 1)[0] + '.hwp'
        output_path = os.path.abspath(output_path)

        # 임시 디렉토리 생성
        temp_dir = tempfile.mkdtemp(prefix="pdf_to_hwp_")
        self._temp_dirs.append(temp_dir)

        try:
            # 1단계: PDF 페이지 수 확인
            page_count = self.pdf_converter.get_page_count(pdf_path)
            self._report_progress(0, 3, f"PDF 분석 완료: {page_count}페이지")

            if show_progress:
                print(f"📄 PDF 파일: {os.path.basename(pdf_path)}")
                print(f"📊 총 {page_count}페이지 발견")

            # 2단계: PDF를 이미지로 변환
            self._report_progress(1, 3, "PDF를 이미지로 변환 중...")
            if show_progress:
                print("\n🔄 PDF를 이미지로 변환 중...")

            results = self.pdf_converter.convert_all_pages(
                pdf_path,
                output_dir=temp_dir,
                show_progress=show_progress,
            )
            image_paths = [path for _, _, path in results]

            # 3단계: 이미지를 HWP로 변환
            self._report_progress(2, 3, "HWP 파일 생성 중...")
            if show_progress:
                print("\n📝 HWP 파일 생성 중...")

            final_path = self.hwp_generator.create_hwp_from_images(
                image_paths,
                output_path,
                show_progress=show_progress,
            )

            self._report_progress(3, 3, "변환 완료!")
            if show_progress:
                print(f"\n✅ 변환 완료: {final_path}")

            return final_path

        finally:
            # 임시 파일 정리
            if not self.keep_temp_files:
                self._cleanup()

    def convert_batch(
        self,
        pdf_paths: List[str],
        output_dir: Optional[str] = None,
        show_progress: bool = True,
    ) -> List[str]:
        """
        여러 PDF 파일을 일괄 변환

        Args:
            pdf_paths: PDF 파일 경로 리스트
            output_dir: 출력 디렉토리 (기본값: 각 PDF와 같은 디렉토리)
            show_progress: 진행 상황 표시 여부

        Returns:
            생성된 HWP 파일 경로 리스트
        """
        results = []

        for i, pdf_path in enumerate(pdf_paths):
            if show_progress:
                print(f"\n{'='*50}")
                print(f"📁 처리 중: {i + 1}/{len(pdf_paths)}")

            output_path = None
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                pdf_name = Path(pdf_path).stem
                output_path = os.path.join(output_dir, f"{pdf_name}.hwp")

            try:
                hwp_path = self.convert(pdf_path, output_path, show_progress)
                results.append(hwp_path)
            except Exception as e:
                if show_progress:
                    print(f"❌ 변환 실패: {pdf_path}")
                    print(f"   오류: {str(e)}")
                results.append(None)

        return results

    def _cleanup(self) -> None:
        """임시 파일 정리"""
        for temp_dir in self._temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        self._temp_dirs.clear()

    def __enter__(self):
        """Context manager 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료 - 리소스 정리"""
        self._cleanup()
        return False


def convert_pdf_to_hwp(
    pdf_path: str,
    output_path: Optional[str] = None,
    dpi: int = 300,
    show_progress: bool = True,
) -> str:
    """
    PDF를 HWP로 변환하는 간편 함수

    Args:
        pdf_path: 입력 PDF 파일 경로
        output_path: 출력 HWP 파일 경로 (기본값: PDF와 같은 이름)
        dpi: 이미지 해상도 (기본값: 300)
        show_progress: 진행 상황 표시 여부

    Returns:
        생성된 HWP 파일 경로
    """
    with PDFToHWPAgent(dpi=dpi) as agent:
        return agent.convert(pdf_path, output_path, show_progress)
