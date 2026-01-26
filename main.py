#!/usr/bin/env python3
"""PDF to HWP Converter - CLI 인터페이스"""

import os
import sys
from pathlib import Path

import click

from pdf_to_hwp import PDFToHWPAgent


@click.group()
@click.version_option(version="1.0.0", prog_name="PDF to HWP Converter")
def cli():
    """PDF 파일을 이미지화하여 HWP로 변환하는 도구"""
    pass


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="출력 HWP 파일 경로 (기본값: PDF와 같은 이름)",
)
@click.option(
    "-d", "--dpi",
    type=int,
    default=300,
    help="이미지 해상도 (기본값: 300)",
)
@click.option(
    "--page-width",
    type=float,
    default=210.0,
    help="페이지 너비 mm (기본값: 210, A4)",
)
@click.option(
    "--page-height",
    type=float,
    default=297.0,
    help="페이지 높이 mm (기본값: 297, A4)",
)
@click.option(
    "--margin",
    type=float,
    default=10.0,
    help="페이지 여백 mm (기본값: 10)",
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    help="진행 상황 표시 끄기",
)
def convert(pdf_path, output, dpi, page_width, page_height, margin, quiet):
    """
    단일 PDF 파일을 HWP로 변환

    \b
    예시:
      python main.py convert document.pdf
      python main.py convert document.pdf -o output.hwp
      python main.py convert document.pdf -d 150 --margin 5
    """
    try:
        agent = PDFToHWPAgent(
            dpi=dpi,
            page_width=page_width,
            page_height=page_height,
            margin=margin,
        )

        with agent:
            result = agent.convert(
                pdf_path,
                output,
                show_progress=not quiet,
            )

        if not quiet:
            click.echo(f"\n✅ 변환 완료: {result}")

    except Exception as e:
        click.echo(f"❌ 오류 발생: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("pdf_paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "-o", "--output-dir",
    type=click.Path(),
    help="출력 디렉토리 (기본값: 각 PDF와 같은 위치)",
)
@click.option(
    "-d", "--dpi",
    type=int,
    default=300,
    help="이미지 해상도 (기본값: 300)",
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    help="진행 상황 표시 끄기",
)
def batch(pdf_paths, output_dir, dpi, quiet):
    """
    여러 PDF 파일을 일괄 변환

    \b
    예시:
      python main.py batch *.pdf
      python main.py batch doc1.pdf doc2.pdf -o ./output/
    """
    if not pdf_paths:
        click.echo("변환할 PDF 파일을 지정하세요.", err=True)
        sys.exit(1)

    try:
        agent = PDFToHWPAgent(dpi=dpi)

        with agent:
            results = agent.convert_batch(
                list(pdf_paths),
                output_dir,
                show_progress=not quiet,
            )

        # 결과 요약
        success = sum(1 for r in results if r is not None)
        failed = len(results) - success

        if not quiet:
            click.echo(f"\n{'='*50}")
            click.echo(f"📊 변환 결과: 성공 {success}개, 실패 {failed}개")

        if failed > 0:
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ 오류 발생: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
def info(pdf_path):
    """
    PDF 파일 정보 표시

    \b
    예시:
      python main.py info document.pdf
    """
    try:
        from pdf_to_hwp.converter import PDFConverter
        import fitz

        converter = PDFConverter()
        page_count = converter.get_page_count(pdf_path)

        click.echo(f"\n📄 PDF 파일 정보")
        click.echo(f"{'='*40}")
        click.echo(f"파일명: {os.path.basename(pdf_path)}")
        click.echo(f"경로: {os.path.abspath(pdf_path)}")
        click.echo(f"크기: {os.path.getsize(pdf_path) / 1024:.1f} KB")
        click.echo(f"페이지 수: {page_count}")

        # 첫 페이지 크기 정보
        with fitz.open(pdf_path) as doc:
            page = doc.load_page(0)
            rect = page.rect
            width_mm = rect.width * 25.4 / 72
            height_mm = rect.height * 25.4 / 72
            click.echo(f"페이지 크기: {width_mm:.1f} x {height_mm:.1f} mm")

    except Exception as e:
        click.echo(f"❌ 오류 발생: {str(e)}", err=True)
        sys.exit(1)


def main():
    """메인 엔트리 포인트"""
    cli()


if __name__ == "__main__":
    main()
