import json
import os
import subprocess
import tempfile
from io import BytesIO
import cloudconvert
import requests
import io
import yt_dlp
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from moviepy.editor import VideoFileClip, AudioFileClip
from tempfile import NamedTemporaryFile
from django.http import StreamingHttpResponse
# Create your views here.
API_KEY = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYzhmNmNjMWY3ZjgyZGUxMmZhNDFiMDAwOWM3MDEyNjRlNzkyMDJmNTIyOTNkYTA1MjBiZjdlZTk0ZjNiMGEzNzUyMGJkNWFjMDQzZjdlZTgiLCJpYXQiOjE3Mjg5MTY4MzUuMzUzMTg2LCJuYmYiOjE3Mjg5MTY4MzUuMzUzMTg4LCJleHAiOjQ4ODQ1OTA0MzUuMzQ2MTk1LCJzdWIiOiI2OTg3Nzk2NCIsInNjb3BlcyI6WyJ1c2VyLnJlYWQiLCJ1c2VyLndyaXRlIiwidGFzay53cml0ZSIsInRhc2sucmVhZCIsIndlYmhvb2sucmVhZCIsIndlYmhvb2sud3JpdGUiLCJwcmVzZXQucmVhZCIsInByZXNldC53cml0ZSJdfQ.dYJXbHKGnXewcr14lUlJA8uNRxM5x8Dw9toTsCFmqfR66C8WHSF9aAh2sOd0FklXJr-6DQiTR0tYs2XzCWGZu94X8JHCbtiiMnk6P4nNgwyq7xYlxBceckkvKnGRHY9Zjn5oECDelt0fYaTC86GjTpdQE4HM3gLJtzc_IWLdAn_dkFIk0-KH8FV45oO7F66sFUoHp24VEBr-40U20U0vvqlJW_TvAVOJwnFSxB1RMeptEmsSTHDVlOck-ur8EWerEGmv3NMmtRdaOT7qZFfy4LQXm7xFumacNqK5F5APwGD5Sl1_uaXmuPFTmDFkwm9ITnJOeOWbY3K94--bC2kvHIIz-YEHus5oEF6cf18EFKluWCoBYZXu4BmA5Vw8wp4XTI5lRGo07MMn2slU8_3oBPMQmTIH9_UbokbWRK-a3-As4GFxbtsbQTapJhdN1mXzsTjPkbr1h4o6yRzVAnGEe4_e6PeedcPAd59nyXsnT7hcjEbLh54r_K15rDl7rztI0vo1ouUEJmr-W2h1mFROXf0KLD6wBRardY3rhz0LFRjbdtR_GHjbg2OhwCnVMvLcpO6dWuT6EDIZC-v6fFDyygwNz9j0SVLadZVFt4X5HgyEOeFo3ty4DJMe3s_T6_HEdfBDDape1REhnRJ1VpXjyY08MRZ4rnNiF9zPlCCFoYM'
cloudconvert.configure(api_key=API_KEY)
def homepage(request):
    return render(request, 'homepage.html')

def audio_homepage(request):
    return render(request, 'audio_only.html')

def video_homepage(request):
    return render(request, 'video_only.html')

def merge_video_audio(video_stream, audio_stream):
    # Сохраняем видео и аудио в временные файлы
    with open("temp_video.mp4", "wb") as video_file:
        video_file.write(video_stream.getbuffer())

    with open("temp_audio.mp3", "wb") as audio_file:
        audio_file.write(audio_stream.getbuffer())

    # Загружаем видео и аудио с помощью MoviePy
    video_clip = VideoFileClip("temp_video.mp4")
    audio_clip = AudioFileClip("temp_audio.mp3")

    # Добавляем аудио к видео
    final_clip = video_clip.set_audio(audio_clip)

    # Сохраняем объединенное видео в память
    output_stream = BytesIO()
    final_clip.write_videofile(output_stream, codec="libx264", audio_codec="aac")

    # Возвращаем поток с видео
    return output_stream


def show_formats(request):
    if request.method == 'POST':
        # Читаем JSON из тела запроса
        data = json.loads(request.body)
        url = data.get('url')

        # Настройки yt-dlp для извлечения информации
        ydl_opts = {
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                formats = info_dict.get('formats', [])

                # Создаем список форматов для ответа
                format_list = []
                for f in formats:
                    format_info = {
                        'format_id': f.get('format_id'),
                        'type': 'Video' if f.get('vcodec') != 'none' else 'Audio',
                        'quality': f.get('height', 'N/A') if f.get('vcodec') != 'none' else f.get('abr', 'N/A'),
                        'format': f.get('ext')
                    }
                    format_list.append(format_info)

                # Возвращаем список форматов как JSON
                return JsonResponse({'formats': format_list, 'video_title': info_dict['title']})
        except Exception as e:
            return JsonResponse({'error': str(e)})

    return JsonResponse({'error': 'Invalid request method'}, status=400)


def generate_video_stream(url, format_id):
    process = subprocess.Popen(
        ["yt-dlp", "-f", format_id, "-o", "-", "--remux-video", "mp4", "--postprocessor-args", "-movflags faststart",
         url],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    while True:
        chunk = process.stdout.read(1024 * 1024)  # Читаем кусками по 1 МБ
        if not chunk:
            break
        yield chunk

def download_video_with_format(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            url = data.get('url')
            format_id = data.get('format_id')

            if not url or not format_id:
                return StreamingHttpResponse("Invalid request: missing URL or format ID", status=400)

            # Настройки yt-dlp для получения информации о видео
            ydl_opts = {
                'format': format_id,
                'quiet': True,
                'noplaylist': True,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                }],
                # Перемещаем метаданные в начало файла
                'postprocessor_args': ['-movflags', 'faststart']
            }

            # Используем yt-dlp для получения информации о видео
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)

                # Проверяем доступные форматы
                selected_format = None
                for f in info_dict['formats']:
                    if str(f['format_id']) == format_id:
                        selected_format = f
                        break

                if not selected_format:
                    return StreamingHttpResponse(f"Format {format_id} not found", status=400)

                # Получаем расширение файла из информации о формате
                file_extension = selected_format.get('ext', 'mp4')  # По умолчанию mp4
                file_name = f"downloaded_video.{file_extension}"

            # Буфер для хранения видео в памяти
            video_buffer = io.BytesIO()

            # Используем subprocess для вызова yt-dlp и записи данных в буфер
            process = subprocess.Popen(
                ["yt-dlp", "-f", format_id, "-o", "-", "--remux-video", "mp4", "--postprocessor-args", "-movflags faststart", url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Чтение stdout и stderr
            stdout, stderr = process.communicate()

            # Проверка на ошибки
            if process.returncode != 0:
                error_message = stderr.decode('utf-8')
                return StreamingHttpResponse(f"Error occurred while downloading: {error_message}", status=500)

            # Записываем stdout в буфер
            video_buffer.write(stdout)

            # Проверяем размер загруженного файла
            video_size = video_buffer.tell()
            if video_size == 0:
                return StreamingHttpResponse("Error: Downloaded file is empty", status=500)

            # Открываем буфер для чтения и отправляем пользователю
            video_buffer.seek(0)
            response = StreamingHttpResponse(video_buffer, content_type=f'video/{file_extension}')
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'

            return response

        except yt_dlp.utils.DownloadError as e:
            return StreamingHttpResponse(f"DownloadError occurred: {str(e)}", status=500)
        except Exception as e:
            return StreamingHttpResponse(f"Error occurred: {str(e)}", status=500)


def download_streams(url, video_format, audio_format):
    try:
        video_path = "video_temp.mp4"
        audio_path = "audio_temp.m4a"

        # Скачиваем видео
        subprocess.run(["yt-dlp", "-f", video_format, "-o", video_path, url], check=True)

        # Скачиваем аудио
        subprocess.run(["yt-dlp", "-f", audio_format, "-o", audio_path, url], check=True)

        return video_path, audio_path

    except subprocess.CalledProcessError as e:
        print(f"Error during download: {e}")
        return None, None
def simple_merge(video_path, audio_path, output_path="merged_output.mp4"):
    try:
        with open(video_path, "rb") as video_file, open(audio_path, "rb") as audio_file, open(output_path, "wb") as output_file:
            video_data = video_file.read()
            audio_data = audio_file.read()

            # Простое объединение (пишем видео и аудио последовательно)
            output_file.write(video_data)
            output_file.write(audio_data)

        if not os.path.exists(output_path):
            print("Error: Merged file not created.")
            return None

        return output_path
    except Exception as e:
        print(f"Error during merging: {e}")
        return None
def process_video(url, video_format, audio_format):
    video_path, audio_path = download_streams(url, video_format, audio_format)
    if video_path and audio_path:
        output_file = simple_merge(video_path, audio_path)
        if output_file:
            print(f"Merged video saved to: {output_file}")
        else:
            print("Merging failed.")
        # Удаляем временные файлы
        os.remove(video_path)
        os.remove(audio_path)
    else:
        print("Failed to download streams.")

# def download_video(request):
#     try:
#         data = json.loads(request.body)
#         url = data.get('url')
#         format_id = data.get('format_id')
#         ydl_opts = {
#             'format': format_id,
#             'quiet': True,
#             'merge_output_format': 'mp4',  # Убедимся, что итоговый файл будет mp4
#             'postprocessors': [
#                 {
#                     'key': 'FFmpegMerger',  # Объединяет аудио и видео
#                 },
#             ],
#             'outtmpl': 'output_video.%(ext)s',  # Шаблон имени файла
#         }
#
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             ydl.download([url])
#
#         return "output_video.mp4"  # Имя загруженного файла
#     except Exception as e:
#         print(f"Error occurred: {e}")
#         return None

def download_video(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            url = data.get("url")
            video_format = data.get("video_format")  # Формат видео
            audio_format = data.get("audio_format")  # Формат аудио

            if not url or not video_format or not audio_format:
                return JsonResponse({"error": "Missing parameters"}, status=400)

            # Скачиваем видео и аудио
            video_path, audio_path = download_streams(url, video_format, audio_format)
            if not video_path or not audio_path:
                return JsonResponse({"error": "Failed to download streams"}, status=500)

            # Объединяем видео и аудио
            output_file = simple_merge(video_path, audio_path)
            if not output_file:
                return JsonResponse({"error": "Failed to merge video and audio"}, status=500)

            # Возвращаем итоговый файл
            def file_iterator(file_path, chunk_size=8192):
                with open(file_path, "rb") as f:
                    while chunk := f.read(chunk_size):
                        yield chunk

            response = StreamingHttpResponse(file_iterator(output_file), content_type="video/mp4")
            response["Content-Disposition"] = f"attachment; filename={os.path.basename(output_file)}"

            # Удаление временных файлов после передачи данных
            # try:
            #     os.remove(video_path)
            #     os.remove(audio_path)
            #     os.remove(output_file)
            # except Exception as e:
            #     print("Error during file cleanup:", e)

            return response

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)