import flet as ft
import flet_video as ftv
import subprocess, os, threading, re, time, asyncio, random
import whisper

OPEN_PHRASES = [
    "Открываю портал в файловую систему...",
    "Пробуждаю душу видео...",
    "Сканирую временные потоки...",
    "Читаю древние метаданные...",
    "Прислушиваюсь к эху контейнера...",
    "Разрываю печати кодека...",
    "Взываю к духам ffmpeg...",
    "Ищу скрытые дорожки...",
    "Осматриваю каркас файла...",
    "Считаю такты времени...",
]

VIDEO_PHRASES = [
    "Отделяю плоть от духа...",
    "Расщепляю видеопоток...",
    "Сдираю видеослой...",
    "Извлекаю движущиеся образы...",
    "Кую видеокаркас заново...",
    "Вырываю кадры из потока...",
    "Замораживаю движение в файл...",
]

AUDIO_PHRASES = [
    "Извлекаю эхо голосов...",
    "Отсекаю аудиодорожку от каркаса...",
    "Ловлю звуковые волны...",
    "Отлавливаю шёпот из глубины...",
    "Вскрываю звуковой слой...",
    "Запечатываю голоса в m4a...",
]

WHISPER_PHRASES = [
    "Призываю оракула Whisper...",
    "Загружаю нейронного демона (medium)...",
    "Оракул вслушивается в шёпот...",
    "Расшифровываю речь смертных...",
    "Ловлю слова в потоке шума...",
    "Пробуждаю слух древних...",
    "Погружаюсь в речевой поток...",
    "Демон шепчет ответы...",
    "Разбираю речь на атомы...",
    "Слушаю сквозь помехи...",
]

SUB_PHRASES = [
    "Начертываю руны субтитров...",
    "Запечатываю слова в SRT...",
    "Записываю свиток текста...",
    "Высекаю буквы на камне...",
    "Связываю слова с временем...",
    "Укладываю строки в хронологию...",
    "Кую субтитры в тишине...",
]

FINAL_PHRASES = [
    "Ритуал завершён.",
    "Душа обрела форму.",
    "Путь открыт.",
    "Печати сорваны. Работа готова.",
]

def main(page: ft.Page):
    page.title = "Split A/V"
    page.window.width = 700
    page.window.height = 750
    page.window.resizable = False

    result_folder = {"path": None}
    state = {"running": False, "start": 0}
    mode_state = {"value": "1"}

    async def pick_input(e):
        r = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["mp4","mkv","avi","mov","webm"])
        if r:
            inp.value = r[0].path
            preview.playlist = [ftv.VideoMedia(r[0].path)]
            if not name.value:
                name.value = os.path.splitext(os.path.basename(r[0].path))[0]
            page.update()

    async def pick_output(e):
        r = await ft.FilePicker().get_directory_path()
        if r:
            out.value = r
            page.update()

    def open_folder(e):
        if result_folder["path"]:
            subprocess.Popen(["explorer", result_folder["path"]])

    async def copy_path(e):
        if result_path.value:
            await ft.Clipboard().set(result_path.value)
            stage_text.value = "Путь скопирован"
            page.update()

    def fmt_ts(t):
        h, m, s = int(t//3600), int((t%3600)//60), t%60
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

    def get_duration(path):
        r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1", path],
                           capture_output=True, text=True)
        return float(r.stdout.strip())

    def log(msg):
        stage_text.value = msg
        page.update()

    def run_ffmpeg(cmd, total, stage_name):
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
        for line in proc.stderr:
            m = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
            if m:
                t = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
                p = min(t/total, 1.0)
                progress.value = p
                stage_text.value = f"{stage_name} {int(p*100)}%"
        proc.wait()

    def work():
        m = mode_state["value"]
        folder = os.path.join(out.value, name.value)
        os.makedirs(folder, exist_ok=True)
        v = os.path.join(folder, "video.mp4")
        a = os.path.join(folder, "audio.m4a")

        log(random.choice(OPEN_PHRASES))
        time.sleep(random.uniform(0.3, 0.7))
        total = get_duration(inp.value)
        time.sleep(random.uniform(0.2, 0.5))

        log(random.choice(VIDEO_PHRASES))
        run_ffmpeg(["ffmpeg","-y","-i",inp.value,"-an","-c:v","copy",v], total, "Расщепляю видеопоток")

        log(random.choice(AUDIO_PHRASES))
        run_ffmpeg(["ffmpeg","-y","-i",inp.value,"-vn","-c:a","copy",a], total, "Отсекаю аудио")

        lang = "—"

        if m in ("2", "3"):
            log(random.choice(WHISPER_PHRASES))
            time.sleep(random.uniform(0.4, 0.9))
            model = whisper.load_model("medium")
            log(random.choice(WHISPER_PHRASES))
            progress.value = None
            result = model.transcribe(a, word_timestamps=True)
            lang = result["language"]

            log(random.choice(SUB_PHRASES))
            srt = os.path.join(folder, "subtitles.srt")
            with open(srt, "w", encoding="utf-8") as f:
                for i, seg in enumerate(result["segments"], 1):
                    f.write(f"{i}\n{fmt_ts(seg['start'])} --> {fmt_ts(seg['end'])}\n{seg['text'].strip()}\n\n")

            if m == "3":
                log(random.choice(SUB_PHRASES))
                txt = os.path.join(folder, "text.txt")
                with open(txt, "w", encoding="utf-8") as f:
                    f.write(result["text"].strip())

        state["running"] = False
        result_folder["path"] = folder
        log(random.choice(FINAL_PHRASES) + f" Язык: {lang}")
        progress.value = 1
        result_path.value = folder
        open_btn.disabled = False
        run_btn.disabled = False
        page.update()

    async def ticker():
        while state["running"]:
            elapsed = int(time.time() - state["start"])
            timer_text.value = f"⏱ {elapsed//60:02d}:{elapsed%60:02d}"
            page.update()
            await asyncio.sleep(1)

    def run(e):
        if not inp.value or not out.value or not name.value:
            stage_text.value = "Заполни все поля"
            page.update()
            return
        run_btn.disabled = True
        open_btn.disabled = True
        result_folder["path"] = None
        result_path.value = ""
        progress.value = 0
        state["running"] = True
        state["start"] = time.time()
        timer_text.value = "⏱ 00:00"
        page.update()
        page.run_task(ticker)
        threading.Thread(target=work, daemon=True).start()

    inp = ft.TextField(label="Видео", read_only=True, expand=True)
    out = ft.TextField(label="Куда", read_only=True, expand=True)
    name = ft.TextField(label="Имя папки", expand=True)
    stage_text = ft.Text("Ожидание", weight=ft.FontWeight.BOLD)
    timer_text = ft.Text("⏱ 00:00")
    progress = ft.ProgressBar(value=0, expand=True)
    preview = ftv.Video(height=180)
    run_btn = ft.Button("Начать", on_click=run)
    open_btn = ft.Button("Открыть папку", on_click=open_folder, disabled=True)
    copy_btn = ft.Button("Копировать путь", on_click=copy_path)
    result_path = ft.TextField(label="Готово в", read_only=True, expand=True)

    mode = ft.RadioGroup(
        value="1",
        on_change=lambda e: mode_state.update({"value": e.control.value}),
        content=ft.Column([
            ft.Radio(value="1", label="1 — только видео + звук"),
            ft.Radio(value="2", label="2 — видео + звук + субтитры (SRT)"),
            ft.Radio(value="3", label="3 — видео + звук + субтитры (SRT) + текст"),
        ])
    )

    page.add(
        ft.Row([inp, ft.Button("Выбрать видео", on_click=pick_input)]),
        ft.Row([out, ft.Button("Выбрать папку", on_click=pick_output)]),
        name,
        mode,
        ft.Row([run_btn, open_btn]),
        ft.Row([stage_text, timer_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        progress,
        ft.Row([result_path, copy_btn]),
        preview,
    )

ft.run(main)