#!/usr/bin/env python3
"""PDF to HWP 변환기 - GUI 애플리케이션"""

import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path

try:
    import tkinterdnd2 as tkdnd

    HAS_DND = True
except ImportError:
    HAS_DND = False

from pdf_to_hwp import PDFToHWPAgent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_drop_data(data: str) -> list[str]:
    """Parse tkdnd drop data into a list of file paths."""
    paths = []
    # tkdnd wraps paths containing spaces in braces: {C:/my path/file.pdf}
    i = 0
    while i < len(data):
        if data[i] == "{":
            end = data.index("}", i)
            paths.append(data[i + 1 : end])
            i = end + 2  # skip } and space
        elif data[i] == " ":
            i += 1
        else:
            end = data.find(" ", i)
            if end == -1:
                end = len(data)
            paths.append(data[i:end])
            i = end + 1
    return [p for p in paths if p.lower().endswith(".pdf")]


def _fmt_size(size_bytes: int) -> str:
    """Return human-readable file size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class PDFIntegratorApp:
    """PDF to HWP 변환기 GUI"""

    def __init__(self):
        # Create root window (with or without DnD support)
        if HAS_DND:
            self.root = tkdnd.TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.title("PDF to HWP 변환기")
        self.root.geometry("900x650")
        self.root.minsize(750, 550)

        # Message queue for thread-safe UI updates
        self._queue: queue.Queue = queue.Queue()
        self._working = False

        # Shared settings variables
        self.dpi_var = tk.IntVar(value=300)
        self.margin_var = tk.DoubleVar(value=10.0)

        self._build_ui()
        self._poll_queue()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self._tab_convert = ttk.Frame(notebook)
        self._tab_batch = ttk.Frame(notebook)
        self._tab_merge = ttk.Frame(notebook)
        self._tab_info = ttk.Frame(notebook)

        notebook.add(self._tab_convert, text=" 변환 ")
        notebook.add(self._tab_batch, text=" 일괄변환 ")
        notebook.add(self._tab_merge, text=" 병합 ")
        notebook.add(self._tab_info, text=" 정보 ")

        self._build_convert_tab()
        self._build_batch_tab()
        self._build_merge_tab()
        self._build_info_tab()

    # ---- Tab 1: Convert ------------------------------------------------

    def _build_convert_tab(self):
        tab = self._tab_convert

        # --- Drop zone ---
        drop_frame = ttk.LabelFrame(tab, text="PDF 파일")
        drop_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self._convert_path_var = tk.StringVar()

        self._drop_label = tk.Label(
            drop_frame,
            text="여기에 PDF 파일을 드래그 & 드롭 하세요\n또는 아래 버튼으로 파일을 선택하세요",
            relief=tk.RIDGE,
            bg="#f0f4ff",
            fg="#555",
            height=4,
            font=("맑은 고딕", 11),
        )
        self._drop_label.pack(fill=tk.X, padx=8, pady=(8, 4))
        self._register_drop(self._drop_label, self._on_convert_drop)

        row_file = ttk.Frame(drop_frame)
        row_file.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Entry(row_file, textvariable=self._convert_path_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4)
        )
        ttk.Button(row_file, text="찾아보기", command=self._browse_convert_pdf).pack(
            side=tk.RIGHT
        )

        # --- Output path ---
        out_frame = ttk.LabelFrame(tab, text="출력 경로")
        out_frame.pack(fill=tk.X, padx=10, pady=5)

        self._convert_out_var = tk.StringVar()
        row_out = ttk.Frame(out_frame)
        row_out.pack(fill=tk.X, padx=8, pady=8)
        ttk.Entry(row_out, textvariable=self._convert_out_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4)
        )
        ttk.Button(row_out, text="찾아보기", command=self._browse_convert_out).pack(
            side=tk.RIGHT
        )

        # --- Settings + button ---
        self._build_settings_row(tab, self._do_convert, "변환")

        # --- Progress ---
        self._convert_progress = ttk.Progressbar(tab, mode="determinate")
        self._convert_progress.pack(fill=tk.X, padx=10, pady=(5, 0))
        self._convert_status = ttk.Label(tab, text="")
        self._convert_status.pack(anchor=tk.W, padx=10)

        # --- Log ---
        self._convert_log = scrolledtext.ScrolledText(
            tab, height=8, state=tk.DISABLED, font=("Consolas", 9)
        )
        self._convert_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 10))

    def _on_convert_drop(self, paths: list[str]):
        if paths:
            self._convert_path_var.set(paths[0])
            base = os.path.splitext(paths[0])[0] + ".hwp"
            self._convert_out_var.set(base)

    def _browse_convert_pdf(self):
        path = filedialog.askopenfilename(
            title="PDF 파일 선택",
            filetypes=[("PDF 파일", "*.pdf")],
        )
        if path:
            self._on_convert_drop([path])

    def _browse_convert_out(self):
        path = filedialog.asksaveasfilename(
            title="출력 파일 저장",
            defaultextension=".hwp",
            filetypes=[("HWP 파일", "*.hwp"), ("HWPX 파일", "*.hwpx")],
        )
        if path:
            self._convert_out_var.set(path)

    def _do_convert(self):
        pdf = self._convert_path_var.get().strip()
        out = self._convert_out_var.get().strip()
        if not pdf:
            messagebox.showwarning("입력 필요", "PDF 파일을 선택하세요.")
            return
        if not os.path.isfile(pdf):
            messagebox.showerror("오류", f"파일을 찾을 수 없습니다:\n{pdf}")
            return
        self._start_work(
            target=self._worker_convert, args=(pdf, out or None)
        )

    def _worker_convert(self, pdf: str, out: str | None):
        try:
            with PDFToHWPAgent(
                dpi=self.dpi_var.get(), margin=self.margin_var.get()
            ) as agent:
                agent.set_progress_callback(self._progress_cb)
                result = agent.convert(pdf, out, show_progress=False)
            self._queue.put(("done", f"변환 완료: {result}"))
        except Exception as e:
            self._queue.put(("error", str(e)))

    # ---- Tab 2: Batch --------------------------------------------------

    def _build_batch_tab(self):
        tab = self._tab_batch

        # File list
        list_frame = ttk.LabelFrame(tab, text="PDF 파일 목록 (드래그 & 드롭 가능)")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        self._batch_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED)
        self._batch_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=8)
        self._register_drop(self._batch_listbox, self._on_batch_drop)

        sb = ttk.Scrollbar(list_frame, command=self._batch_listbox.yview)
        sb.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 4), pady=8)
        self._batch_listbox.config(yscrollcommand=sb.set)

        btn_col = ttk.Frame(list_frame)
        btn_col.pack(side=tk.LEFT, padx=(4, 8), pady=8)
        ttk.Button(btn_col, text="추가", width=8, command=self._batch_add).pack(pady=2)
        ttk.Button(btn_col, text="제거", width=8, command=self._batch_remove).pack(pady=2)
        ttk.Button(btn_col, text="전체 삭제", width=8, command=self._batch_clear).pack(pady=2)

        # Output dir
        out_frame = ttk.LabelFrame(tab, text="출력 디렉토리")
        out_frame.pack(fill=tk.X, padx=10, pady=5)
        self._batch_out_var = tk.StringVar()
        row_out = ttk.Frame(out_frame)
        row_out.pack(fill=tk.X, padx=8, pady=8)
        ttk.Entry(row_out, textvariable=self._batch_out_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4)
        )
        ttk.Button(row_out, text="찾아보기", command=self._browse_batch_out).pack(
            side=tk.RIGHT
        )

        # Settings + button
        self._build_settings_row(tab, self._do_batch, "일괄 변환")

        # Progress
        self._batch_progress = ttk.Progressbar(tab, mode="determinate")
        self._batch_progress.pack(fill=tk.X, padx=10, pady=(5, 0))
        self._batch_status = ttk.Label(tab, text="")
        self._batch_status.pack(anchor=tk.W, padx=10, pady=(0, 10))

    def _on_batch_drop(self, paths: list[str]):
        for p in paths:
            self._batch_listbox.insert(tk.END, p)

    def _batch_add(self):
        paths = filedialog.askopenfilenames(
            title="PDF 파일 선택", filetypes=[("PDF 파일", "*.pdf")]
        )
        for p in paths:
            self._batch_listbox.insert(tk.END, p)

    def _batch_remove(self):
        for i in reversed(self._batch_listbox.curselection()):
            self._batch_listbox.delete(i)

    def _batch_clear(self):
        self._batch_listbox.delete(0, tk.END)

    def _browse_batch_out(self):
        d = filedialog.askdirectory(title="출력 디렉토리 선택")
        if d:
            self._batch_out_var.set(d)

    def _do_batch(self):
        items = self._batch_listbox.get(0, tk.END)
        if not items:
            messagebox.showwarning("입력 필요", "PDF 파일을 추가하세요.")
            return
        out_dir = self._batch_out_var.get().strip() or None
        self._start_work(target=self._worker_batch, args=(list(items), out_dir))

    def _worker_batch(self, pdf_list: list[str], out_dir: str | None):
        try:
            with PDFToHWPAgent(
                dpi=self.dpi_var.get(), margin=self.margin_var.get()
            ) as agent:
                agent.set_progress_callback(self._progress_cb)
                results = agent.convert_batch(pdf_list, out_dir, show_progress=False)
            ok = sum(1 for r in results if r is not None)
            self._queue.put(("done", f"일괄 변환 완료: {ok}/{len(results)} 성공"))
        except Exception as e:
            self._queue.put(("error", str(e)))

    # ---- Tab 3: Merge --------------------------------------------------

    def _build_merge_tab(self):
        tab = self._tab_merge

        # File list with reorder
        list_frame = ttk.LabelFrame(tab, text="PDF 파일 목록 (드래그 & 드롭 가능, 순서대로 병합)")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        self._merge_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        self._merge_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=8)
        self._register_drop(self._merge_listbox, self._on_merge_drop)

        sb = ttk.Scrollbar(list_frame, command=self._merge_listbox.yview)
        sb.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 4), pady=8)
        self._merge_listbox.config(yscrollcommand=sb.set)

        btn_col = ttk.Frame(list_frame)
        btn_col.pack(side=tk.LEFT, padx=(4, 8), pady=8)
        ttk.Button(btn_col, text="추가", width=8, command=self._merge_add).pack(pady=2)
        ttk.Button(btn_col, text="제거", width=8, command=self._merge_remove).pack(pady=2)
        ttk.Button(btn_col, text="▲ 위로", width=8, command=self._merge_up).pack(pady=2)
        ttk.Button(btn_col, text="▼ 아래로", width=8, command=self._merge_down).pack(pady=2)
        ttk.Button(btn_col, text="전체 삭제", width=8, command=self._merge_clear).pack(pady=2)

        # Output file
        out_frame = ttk.LabelFrame(tab, text="출력 파일")
        out_frame.pack(fill=tk.X, padx=10, pady=5)
        self._merge_out_var = tk.StringVar()
        row_out = ttk.Frame(out_frame)
        row_out.pack(fill=tk.X, padx=8, pady=8)
        ttk.Entry(row_out, textvariable=self._merge_out_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4)
        )
        ttk.Button(row_out, text="찾아보기", command=self._browse_merge_out).pack(
            side=tk.RIGHT
        )

        # Settings + button
        self._build_settings_row(tab, self._do_merge, "병합")

        # Progress
        self._merge_progress = ttk.Progressbar(tab, mode="determinate")
        self._merge_progress.pack(fill=tk.X, padx=10, pady=(5, 0))
        self._merge_status = ttk.Label(tab, text="")
        self._merge_status.pack(anchor=tk.W, padx=10, pady=(0, 10))

    def _on_merge_drop(self, paths: list[str]):
        for p in paths:
            self._merge_listbox.insert(tk.END, p)

    def _merge_add(self):
        paths = filedialog.askopenfilenames(
            title="PDF 파일 선택", filetypes=[("PDF 파일", "*.pdf")]
        )
        for p in paths:
            self._merge_listbox.insert(tk.END, p)

    def _merge_remove(self):
        sel = self._merge_listbox.curselection()
        if sel:
            self._merge_listbox.delete(sel[0])

    def _merge_up(self):
        sel = self._merge_listbox.curselection()
        if sel and sel[0] > 0:
            i = sel[0]
            item = self._merge_listbox.get(i)
            self._merge_listbox.delete(i)
            self._merge_listbox.insert(i - 1, item)
            self._merge_listbox.select_set(i - 1)

    def _merge_down(self):
        sel = self._merge_listbox.curselection()
        if sel and sel[0] < self._merge_listbox.size() - 1:
            i = sel[0]
            item = self._merge_listbox.get(i)
            self._merge_listbox.delete(i)
            self._merge_listbox.insert(i + 1, item)
            self._merge_listbox.select_set(i + 1)

    def _merge_clear(self):
        self._merge_listbox.delete(0, tk.END)

    def _browse_merge_out(self):
        path = filedialog.asksaveasfilename(
            title="출력 파일 저장",
            defaultextension=".hwp",
            filetypes=[("HWP 파일", "*.hwp"), ("HWPX 파일", "*.hwpx")],
        )
        if path:
            self._merge_out_var.set(path)

    def _do_merge(self):
        items = self._merge_listbox.get(0, tk.END)
        if not items:
            messagebox.showwarning("입력 필요", "PDF 파일을 추가하세요.")
            return
        out = self._merge_out_var.get().strip()
        if not out:
            messagebox.showwarning("입력 필요", "출력 파일 경로를 지정하세요.")
            return
        self._start_work(target=self._worker_merge, args=(list(items), out))

    def _worker_merge(self, pdf_list: list[str], out: str):
        try:
            with PDFToHWPAgent(
                dpi=self.dpi_var.get(), margin=self.margin_var.get()
            ) as agent:
                agent.set_progress_callback(self._progress_cb)
                result = agent.merge_pdfs(pdf_list, out, show_progress=False)
            self._queue.put(("done", f"병합 완료: {result}"))
        except Exception as e:
            self._queue.put(("error", str(e)))

    # ---- Tab 4: Info ---------------------------------------------------

    def _build_info_tab(self):
        tab = self._tab_info

        # File chooser
        file_frame = ttk.LabelFrame(tab, text="PDF 파일")
        file_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        self._info_path_var = tk.StringVar()

        drop_lbl = tk.Label(
            file_frame,
            text="PDF 파일을 드래그 & 드롭 하거나 아래에서 선택하세요",
            relief=tk.RIDGE,
            bg="#f0f4ff",
            fg="#555",
            height=2,
            font=("맑은 고딕", 10),
        )
        drop_lbl.pack(fill=tk.X, padx=8, pady=(8, 4))
        self._register_drop(drop_lbl, self._on_info_drop)

        row = ttk.Frame(file_frame)
        row.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Entry(row, textvariable=self._info_path_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4)
        )
        ttk.Button(row, text="찾아보기", command=self._browse_info).pack(side=tk.RIGHT)

        ttk.Button(tab, text="정보 조회", command=self._do_info).pack(padx=10, pady=5)

        # Info display
        self._info_text = scrolledtext.ScrolledText(
            tab, height=15, state=tk.DISABLED, font=("Consolas", 10)
        )
        self._info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

    def _on_info_drop(self, paths: list[str]):
        if paths:
            self._info_path_var.set(paths[0])
            self._do_info()

    def _browse_info(self):
        path = filedialog.askopenfilename(
            title="PDF 파일 선택", filetypes=[("PDF 파일", "*.pdf")]
        )
        if path:
            self._info_path_var.set(path)

    def _do_info(self):
        pdf = self._info_path_var.get().strip()
        if not pdf:
            messagebox.showwarning("입력 필요", "PDF 파일을 선택하세요.")
            return
        if not os.path.isfile(pdf):
            messagebox.showerror("오류", f"파일을 찾을 수 없습니다:\n{pdf}")
            return
        try:
            agent = PDFToHWPAgent()
            info = agent.get_pdf_info(pdf)
            text = (
                f"파일명:    {info['filename']}\n"
                f"경로:      {info['filepath']}\n"
                f"페이지 수: {info['page_count']}\n"
                f"파일 크기: {_fmt_size(info['file_size'])}\n"
            )
            self._info_text.config(state=tk.NORMAL)
            self._info_text.delete("1.0", tk.END)
            self._info_text.insert(tk.END, text)
            self._info_text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("오류", str(e))

    # ------------------------------------------------------------------
    # Shared widgets & helpers
    # ------------------------------------------------------------------

    def _build_settings_row(self, parent, command, button_text: str):
        """Build a settings row with DPI, margin, and action button."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(frame, text="DPI:").pack(side=tk.LEFT)
        dpi_spin = ttk.Spinbox(
            frame, from_=72, to=600, width=6, textvariable=self.dpi_var
        )
        dpi_spin.pack(side=tk.LEFT, padx=(2, 12))

        ttk.Label(frame, text="여백(mm):").pack(side=tk.LEFT)
        margin_spin = ttk.Spinbox(
            frame, from_=0, to=50, width=6, increment=0.5,
            textvariable=self.margin_var,
        )
        margin_spin.pack(side=tk.LEFT, padx=(2, 12))

        ttk.Label(frame, text="페이지: A4").pack(side=tk.LEFT, padx=(0, 12))

        btn = ttk.Button(frame, text=button_text, command=command)
        btn.pack(side=tk.RIGHT)

    def _register_drop(self, widget, callback):
        """Register drag-and-drop on a widget if tkinterdnd2 is available."""
        if not HAS_DND:
            return
        widget.drop_target_register(tkdnd.DND_FILES)
        widget.dnd_bind("<<Drop>>", lambda e: callback(_parse_drop_data(e.data)))

    # ------------------------------------------------------------------
    # Threading / progress
    # ------------------------------------------------------------------

    def _start_work(self, target, args=()):
        if self._working:
            messagebox.showinfo("작업 중", "이전 작업이 진행 중입니다.")
            return
        self._working = True
        # Reset progress bars
        for pb in (self._convert_progress, self._batch_progress, self._merge_progress):
            pb["value"] = 0
        for lbl in (self._convert_status, self._batch_status, self._merge_status):
            lbl.config(text="작업 중...")
        # Clear convert log
        self._convert_log.config(state=tk.NORMAL)
        self._convert_log.delete("1.0", tk.END)
        self._convert_log.config(state=tk.DISABLED)

        t = threading.Thread(target=target, args=args, daemon=True)
        t.start()

    def _progress_cb(self, current: int, total: int, message: str):
        """Called from worker thread via agent.set_progress_callback."""
        self._queue.put(("progress", current, total, message))

    def _poll_queue(self):
        """Poll the message queue and update UI."""
        try:
            while True:
                msg = self._queue.get_nowait()
                kind = msg[0]
                if kind == "progress":
                    _, cur, total, text = msg
                    pct = int(cur / max(total, 1) * 100)
                    for pb in (self._convert_progress, self._batch_progress, self._merge_progress):
                        pb["value"] = pct
                    for lbl in (self._convert_status, self._batch_status, self._merge_status):
                        lbl.config(text=text)
                    self._log(text)
                elif kind == "done":
                    self._working = False
                    for pb in (self._convert_progress, self._batch_progress, self._merge_progress):
                        pb["value"] = 100
                    for lbl in (self._convert_status, self._batch_status, self._merge_status):
                        lbl.config(text=msg[1])
                    self._log(msg[1])
                    messagebox.showinfo("완료", msg[1])
                elif kind == "error":
                    self._working = False
                    for lbl in (self._convert_status, self._batch_status, self._merge_status):
                        lbl.config(text="오류 발생")
                    self._log(f"오류: {msg[1]}")
                    messagebox.showerror("오류", msg[1])
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _log(self, text: str):
        self._convert_log.config(state=tk.NORMAL)
        self._convert_log.insert(tk.END, text + "\n")
        self._convert_log.see(tk.END)
        self._convert_log.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self):
        self.root.mainloop()


def main():
    app = PDFIntegratorApp()
    if not HAS_DND:
        print(
            "[INFO] tkinterdnd2가 설치되지 않아 드래그 & 드롭이 비활성화됩니다.\n"
            "       pip install tkinterdnd2 로 설치할 수 있습니다."
        )
    app.run()


if __name__ == "__main__":
    main()
