import yt_dlp
from yt_dlp.utils import DownloadError
from pydub import AudioSegment
import os
import base64
# import imageio_ffmpeg
# AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
# AudioSegment.ffprobe = imageio_ffmpeg.get_ffmpeg_exe()

try:
    import streamlit as st
except ImportError:
    st = None

DOWNLOAD_DIR = 'downloades'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COOKIE_FILE_PATH = os.path.join(DOWNLOAD_DIR, "cookies.txt")


def setup_youtube_cookies():
    """
    Reads base64-encoded cookies from Streamlit secrets (YOUTUBE_COOKIES),
    decodes them, and writes them to a cookies.txt file.
    Returns the path to the cookie file, or None if not configured.
    """
    if st is None:
        return None

    try:
        cookies_b64 = st.secrets.get("YOUTUBE_COOKIES", None)
    except Exception:
        cookies_b64 = None

    if not cookies_b64:
        return None

    try:
        cookies_data = base64.b64decode(cookies_b64.strip())
        with open(COOKIE_FILE_PATH, "wb") as f:
            f.write(cookies_data)
        return COOKIE_FILE_PATH
    except Exception as e:
        print(f"Failed to set up YouTube cookies: {e}")
        return None


def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")

    cookie_file = setup_youtube_cookies()

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "js_runtimes": {"node": {}},
    }

    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            filename = os.path.splitext(filename)[0] + ".wav"
            return filename

    except DownloadError as e:
        raise Exception(f"Failed to download YouTube video.\n{e}")


def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)  # 16khz
    audio.export(output_path, format="wav")
    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000

    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start: start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")

        chunks.append(chunk_path)

    return chunks


def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks

# print(process_input("https://www.youtube.com/shorts/yGV9YMy4WNA"))