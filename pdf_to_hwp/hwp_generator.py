"""이미지를 HWP 파일로 변환하는 모듈"""

import os
from pathlib import Path
from typing import List, Optional, Tuple, Union

from PIL import Image
from tqdm import tqdm

try:
    from pyhwpx import Hwp
    PYHWPX_AVAILABLE = True
except ImportError:
    PYHWPX_AVAILABLE = False


class HWPGenerator:
    """이미지들을 HWP 파일로 생성하는 클래스"""

    def __init__(
        self,
        page_width: float = 210.0,
        page_height: float = 297.0,
        margin: float = 10.0,
    ):
        """
        HWPGenerator 초기화

        Args:
            page_width: 페이지 너비 (mm, 기본값: A4 210mm)
            page_height: 페이지 높이 (mm, 기본값: A4 297mm)
            margin: 여백 (mm, 기본값: 10mm)
        """
        self.page_width = page_width
        self.page_height = page_height
        self.margin = margin
        self.content_width = page_width - (2 * margin)
        self.content_height = page_height - (2 * margin)

    def _calculate_image_size(
        self, image: Image.Image
    ) -> Tuple[float, float]:
        """
        이미지가 페이지에 맞도록 크기 계산

        Args:
            image: PIL Image 객체

        Returns:
            (너비, 높이) in mm
        """
        img_width, img_height = image.size
        aspect_ratio = img_width / img_height

        # 페이지에 맞게 스케일링
        if aspect_ratio > (self.content_width / self.content_height):
            # 너비에 맞춤
            new_width = self.content_width
            new_height = new_width / aspect_ratio
        else:
            # 높이에 맞춤
            new_height = self.content_height
            new_width = new_height * aspect_ratio

        return new_width, new_height

    def create_hwp_with_pyhwpx(
        self,
        images: List[Union[str, Image.Image]],
        output_path: str,
        show_progress: bool = True,
    ) -> str:
        """
        pyhwpx를 사용하여 HWP 파일 생성

        Args:
            images: 이미지 파일 경로 또는 PIL Image 객체 리스트
            output_path: 출력 HWP 파일 경로
            show_progress: 진행 상황 표시 여부

        Returns:
            생성된 HWP 파일 경로
        """
        if not PYHWPX_AVAILABLE:
            raise ImportError(
                "pyhwpx가 설치되어 있지 않습니다. "
                "'pip install pyhwpx'로 설치하세요."
            )

        hwp = Hwp(visible=False)

        try:
            items = images
            if show_progress:
                items = tqdm(images, desc="HWP 생성 중", unit="page")

            for i, img_source in enumerate(items):
                # 이미지 경로 또는 객체 처리
                if isinstance(img_source, str):
                    img_path = img_source
                    img = Image.open(img_source)
                else:
                    # PIL Image인 경우 임시 파일로 저장
                    import tempfile
                    temp_file = tempfile.NamedTemporaryFile(
                        suffix=".png", delete=False
                    )
                    img_source.save(temp_file.name)
                    img_path = temp_file.name
                    img = img_source

                # 이미지 크기 계산
                width_mm, height_mm = self._calculate_image_size(img)

                # 첫 페이지가 아니면 새 페이지 추가
                if i > 0:
                    hwp.insert_ctrl("BREAK", "")

                # 이미지 삽입
                hwp.insert_picture(
                    img_path,
                    width=int(width_mm * 283.46),  # mm to HWPUNIT
                    height=int(height_mm * 283.46),
                    sizeoption=0,
                    treat_as_char=False,
                )

            # HWP 파일 저장
            hwp.save_as(output_path)

        finally:
            hwp.quit()

        return output_path

    def create_hwp_from_images(
        self,
        images: List[Union[str, Image.Image]],
        output_path: str,
        show_progress: bool = True,
    ) -> str:
        """
        이미지들로부터 HWP 파일 생성

        Args:
            images: 이미지 파일 경로 또는 PIL Image 객체 리스트
            output_path: 출력 HWP 파일 경로
            show_progress: 진행 상황 표시 여부

        Returns:
            생성된 HWP 파일 경로
        """
        if PYHWPX_AVAILABLE:
            return self.create_hwp_with_pyhwpx(images, output_path, show_progress)
        else:
            # pyhwpx가 없는 경우 대체 방법 사용
            return self.create_hwp_fallback(images, output_path, show_progress)

    def create_hwp_fallback(
        self,
        images: List[Union[str, Image.Image]],
        output_path: str,
        show_progress: bool = True,
    ) -> str:
        """
        pyhwpx 없이 HWP 파일 생성 (HWPX 포맷 사용)

        HWPX는 HWP의 OpenDocument 기반 포맷으로 XML 구조입니다.

        Args:
            images: 이미지 파일 경로 또는 PIL Image 객체 리스트
            output_path: 출력 HWP 파일 경로
            show_progress: 진행 상황 표시 여부

        Returns:
            생성된 HWP 파일 경로 (.hwpx)
        """
        import zipfile
        import tempfile
        from xml.etree import ElementTree as ET

        # HWPX는 .hwpx 확장자 사용
        if not output_path.endswith('.hwpx'):
            output_path = output_path.rsplit('.', 1)[0] + '.hwpx'

        temp_dir = tempfile.mkdtemp(prefix="hwpx_")

        try:
            # HWPX 기본 구조 생성
            self._create_hwpx_structure(temp_dir, images, show_progress)

            # ZIP으로 압축하여 HWPX 생성
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zf.write(file_path, arcname)

        finally:
            # 임시 디렉토리 정리
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

        return output_path

    def _create_hwpx_structure(
        self,
        temp_dir: str,
        images: List[Union[str, Image.Image]],
        show_progress: bool = True,
    ):
        """HWPX 파일의 내부 구조 생성"""
        import shutil

        # 필요한 디렉토리 생성
        os.makedirs(os.path.join(temp_dir, "Contents"), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, "Contents", "BinData"), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, "META-INF"), exist_ok=True)

        # mimetype 파일 생성
        with open(os.path.join(temp_dir, "mimetype"), "w") as f:
            f.write("application/hwp+zip")

        # 이미지 복사 및 section.xml 생성
        image_refs = []
        items = enumerate(images)
        if show_progress:
            items = tqdm(list(items), desc="HWPX 생성 중", unit="page")

        for i, img_source in items:
            img_filename = f"image{i + 1}.png"
            img_dest = os.path.join(temp_dir, "Contents", "BinData", img_filename)

            if isinstance(img_source, str):
                shutil.copy2(img_source, img_dest)
                img = Image.open(img_source)
            else:
                img_source.save(img_dest, "PNG")
                img = img_source

            width_mm, height_mm = self._calculate_image_size(img)
            image_refs.append({
                "filename": img_filename,
                "width": width_mm,
                "height": height_mm,
                "index": i + 1
            })

        # content.hpf 생성 (HWPX 메인 문서)
        self._create_content_hpf(temp_dir, image_refs)

        # section0.xml 생성 (본문 내용)
        self._create_section_xml(temp_dir, image_refs)

        # header.xml 생성
        self._create_header_xml(temp_dir)

        # META-INF/container.xml 생성
        self._create_container_xml(temp_dir)

        # _rels/.rels 생성
        os.makedirs(os.path.join(temp_dir, "_rels"), exist_ok=True)
        self._create_rels(temp_dir)

    def _create_content_hpf(self, temp_dir: str, image_refs: list):
        """content.hpf 파일 생성"""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<opf:package version="1.0" unique-identifier="bookid" xmlns:opf="http://www.idpf.org/2007/opf">
  <opf:metadata>
    <opf:title>PDF to HWP Converted Document</opf:title>
    <opf:language>ko</opf:language>
  </opf:metadata>
  <opf:manifest>
    <opf:item id="header" href="Contents/header.xml" media-type="application/xml"/>
    <opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/>
"""
        for ref in image_refs:
            content += f'    <opf:item id="image{ref["index"]}" href="Contents/BinData/{ref["filename"]}" media-type="image/png"/>\n'

        content += """  </opf:manifest>
  <opf:spine>
    <opf:itemref idref="section0"/>
  </opf:spine>
</opf:package>
"""
        with open(os.path.join(temp_dir, "Contents", "content.hpf"), "w", encoding="utf-8") as f:
            f.write(content)

    def _create_section_xml(self, temp_dir: str, image_refs: list):
        """section0.xml 파일 생성 (본문)"""
        # HWPUNIT: 1mm = 283.46 HWPUNIT (7200 HWPUNIT = 1 inch)
        hwpunit_per_mm = 283.46

        content = """<?xml version="1.0" encoding="UTF-8"?>
<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"
        xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"
        xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core">
"""
        for i, ref in enumerate(image_refs):
            width_unit = int(ref["width"] * hwpunit_per_mm)
            height_unit = int(ref["height"] * hwpunit_per_mm)

            content += f"""  <hp:p>
    <hp:run>
      <hp:pic>
        <hp:picSz width="{width_unit}" height="{height_unit}"/>
        <hp:binItem binId="{ref['index']}" format="PNG"/>
      </hp:pic>
    </hp:run>
  </hp:p>
"""
            # 페이지 구분 (마지막 페이지 제외)
            if i < len(image_refs) - 1:
                content += """  <hp:p>
    <hp:run>
      <hp:ctrl>
        <hc:colPr type="PAGE"/>
      </hp:ctrl>
    </hp:run>
  </hp:p>
"""

        content += """</hs:sec>
"""
        with open(os.path.join(temp_dir, "Contents", "section0.xml"), "w", encoding="utf-8") as f:
            f.write(content)

    def _create_header_xml(self, temp_dir: str):
        """header.xml 파일 생성"""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head">
  <hh:docInfo>
    <hh:generator>PDF to HWP Converter</hh:generator>
  </hh:docInfo>
  <hh:docSummary>
    <hh:title>PDF to HWP Converted Document</hh:title>
  </hh:docSummary>
</hh:head>
"""
        with open(os.path.join(temp_dir, "Contents", "header.xml"), "w", encoding="utf-8") as f:
            f.write(content)

    def _create_container_xml(self, temp_dir: str):
        """META-INF/container.xml 생성"""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="Contents/content.hpf" media-type="application/hwp+zip"/>
  </rootfiles>
</container>
"""
        with open(os.path.join(temp_dir, "META-INF", "container.xml"), "w", encoding="utf-8") as f:
            f.write(content)

    def _create_rels(self, temp_dir: str):
        """_rels/.rels 생성"""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://www.hancom.co.kr/hwpml/2011/package" Target="Contents/content.hpf"/>
</Relationships>
"""
        with open(os.path.join(temp_dir, "_rels", ".rels"), "w", encoding="utf-8") as f:
            f.write(content)


def images_to_hwp(
    images: List[Union[str, Image.Image]],
    output_path: str,
    show_progress: bool = True,
) -> str:
    """
    이미지 리스트를 HWP 파일로 변환하는 간편 함수

    Args:
        images: 이미지 파일 경로 또는 PIL Image 객체 리스트
        output_path: 출력 HWP 파일 경로
        show_progress: 진행 상황 표시 여부

    Returns:
        생성된 HWP 파일 경로
    """
    generator = HWPGenerator()
    return generator.create_hwp_from_images(images, output_path, show_progress)
