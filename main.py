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
@click.argument("pdf_paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    required=True,
    help="출력 HWP 파일 경로",
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
@click.option(
    "--no-reorder",
    is_flag=True,
    help="순서 재배열 건너뛰기 (입력 순서 그대로 사용)",
)
def merge(pdf_paths, output, dpi, page_width, page_height, margin, quiet, no_reorder):
    """
    여러 PDF 파일을 하나의 HWP로 병합

    \b
    예시:
      python main.py merge doc1.pdf doc2.pdf doc3.pdf -o merged.hwp
      python main.py merge *.pdf -o output.hwp --no-reorder
    """
    if not pdf_paths:
        click.echo("병합할 PDF 파일을 지정하세요.", err=True)
        sys.exit(1)

    if len(pdf_paths) < 2:
        click.echo("병합하려면 2개 이상의 PDF 파일이 필요합니다.", err=True)
        sys.exit(1)

    try:
        pdf_list = list(pdf_paths)

        # 순서 재배열 (--no-reorder 옵션이 없는 경우)
        if not no_reorder:
            pdf_list = interactive_reorder(pdf_list)
            if pdf_list is None:
                click.echo("\n❌ 병합이 취소되었습니다.")
                sys.exit(0)

        agent = PDFToHWPAgent(
            dpi=dpi,
            page_width=page_width,
            page_height=page_height,
            margin=margin,
        )

        with agent:
            result = agent.merge_pdfs(
                pdf_list,
                output,
                show_progress=not quiet,
            )

        if not quiet:
            click.echo(f"\n✅ 병합 완료: {result}")

    except Exception as e:
        click.echo(f"❌ 오류 발생: {str(e)}", err=True)
        sys.exit(1)


def interactive_reorder(pdf_paths: list) -> list:
    """
    대화형 PDF 순서 재배열

    Args:
        pdf_paths: PDF 파일 경로 리스트

    Returns:
        재배열된 PDF 파일 경로 리스트 (취소 시 None)
    """
    from pdf_to_hwp.converter import PDFConverter

    converter = PDFConverter()
    current_order = list(pdf_paths)

    # PDF 정보 수집
    pdf_info = []
    for path in current_order:
        try:
            page_count = converter.get_page_count(path)
            file_size = os.path.getsize(path) / 1024  # KB
            pdf_info.append({
                "path": path,
                "name": os.path.basename(path),
                "pages": page_count,
                "size": file_size,
            })
        except Exception as e:
            click.echo(f"⚠️  {path} 정보 읽기 실패: {e}")
            pdf_info.append({
                "path": path,
                "name": os.path.basename(path),
                "pages": "?",
                "size": 0,
            })

    while True:
        # 현재 순서 표시
        click.echo(f"\n{'='*60}")
        click.echo("📋 현재 PDF 순서 (병합될 순서)")
        click.echo(f"{'='*60}")

        total_pages = 0
        for i, info in enumerate(pdf_info):
            pages = info["pages"]
            if isinstance(pages, int):
                total_pages += pages
            click.echo(
                f"  {i + 1}. {info['name']}"
                f"  ({info['pages']}페이지, {info['size']:.1f}KB)"
            )

        click.echo(f"{'='*60}")
        click.echo(f"📊 총 {len(pdf_info)}개 파일, {total_pages}페이지")
        click.echo(f"{'='*60}")

        # 명령어 안내
        click.echo("\n📝 명령어:")
        click.echo("  [순서 입력]  예: 3 1 2 4  → 3번을 맨 앞으로")
        click.echo("  [swap A B]  예: swap 1 3  → 1번과 3번 위치 교환")
        click.echo("  [move A B]  예: move 3 1  → 3번을 1번 위치로 이동")
        click.echo("  [reverse]   전체 순서 뒤집기")
        click.echo("  [ok/확인]   현재 순서로 병합 시작")
        click.echo("  [cancel/취소] 병합 취소")

        # 입력 받기
        user_input = click.prompt("\n➡️  명령어 입력", default="ok").strip().lower()

        if user_input in ("ok", "확인", "y", "yes"):
            # 현재 순서로 확정
            return [info["path"] for info in pdf_info]

        elif user_input in ("cancel", "취소", "n", "no", "q", "quit"):
            return None

        elif user_input == "reverse":
            pdf_info.reverse()
            click.echo("🔄 순서가 뒤집혔습니다.")

        elif user_input.startswith("swap "):
            try:
                parts = user_input.split()
                if len(parts) != 3:
                    raise ValueError("형식: swap A B")
                a, b = int(parts[1]) - 1, int(parts[2]) - 1
                if not (0 <= a < len(pdf_info) and 0 <= b < len(pdf_info)):
                    raise ValueError("잘못된 번호입니다.")
                pdf_info[a], pdf_info[b] = pdf_info[b], pdf_info[a]
                click.echo(f"🔄 {a + 1}번과 {b + 1}번을 교환했습니다.")
            except ValueError as e:
                click.echo(f"⚠️  오류: {e}")

        elif user_input.startswith("move "):
            try:
                parts = user_input.split()
                if len(parts) != 3:
                    raise ValueError("형식: move A B (A를 B위치로 이동)")
                src, dst = int(parts[1]) - 1, int(parts[2]) - 1
                if not (0 <= src < len(pdf_info) and 0 <= dst < len(pdf_info)):
                    raise ValueError("잘못된 번호입니다.")
                item = pdf_info.pop(src)
                pdf_info.insert(dst, item)
                click.echo(f"🔄 {src + 1}번을 {dst + 1}번 위치로 이동했습니다.")
            except ValueError as e:
                click.echo(f"⚠️  오류: {e}")

        else:
            # 순서 직접 입력 (예: "3 1 2 4")
            try:
                new_order = [int(x) - 1 for x in user_input.split()]

                # 검증
                if len(new_order) != len(pdf_info):
                    raise ValueError(
                        f"모든 파일 번호를 입력하세요. "
                        f"(필요: {len(pdf_info)}개, 입력: {len(new_order)}개)"
                    )

                if sorted(new_order) != list(range(len(pdf_info))):
                    raise ValueError("1부터 N까지 각 번호를 한 번씩만 사용하세요.")

                # 순서 재배열
                pdf_info = [pdf_info[i] for i in new_order]
                click.echo("🔄 순서가 변경되었습니다.")

            except ValueError as e:
                click.echo(f"⚠️  오류: {e}")
                click.echo("    숫자를 공백으로 구분하여 입력하세요. 예: 3 1 2 4")


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
