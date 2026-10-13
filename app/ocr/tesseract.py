from __future__ import annotations

import statistics
from dataclasses import dataclass
from pathlib import Path

import pytesseract
from PIL import Image, ImageOps
from pytesseract import Output, TesseractNotFoundError

from app.config import Settings


class OCRProcessingError(RuntimeError):
    pass


@dataclass(slots=True)
class OCRResult:
    text: str
    small_text: str | None


class TesseractOCR:
    def __init__(self, settings: Settings) -> None:
        self._lang = settings.tesseract_lang
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    def recognize_image_sync(self, image_path: Path) -> OCRResult:
        try:
            with Image.open(image_path) as source:
                image = ImageOps.grayscale(source)
                image = ImageOps.autocontrast(image)
                text = pytesseract.image_to_string(image, lang=self._lang).strip()
                data = pytesseract.image_to_data(image, lang=self._lang, output_type=Output.DICT)
        except TesseractNotFoundError as exc:
            raise OCRProcessingError(
                "Tesseract OCR не найден. Установите tesseract и укажите TESSERACT_CMD при необходимости."
            ) from exc
        except Exception as exc:
            raise OCRProcessingError(f"Не удалось распознать изображение: {exc}") from exc

        if not text:
            raise OCRProcessingError("Не удалось распознать текст на изображении.")

        return OCRResult(text=text, small_text=self._extract_small_text(data))

    @staticmethod
    def _extract_small_text(data: dict[str, list]) -> str | None:
        # На фотографиях размер шрифта можно оценить только приблизительно по высоте OCR-боксов.
        words: list[tuple[str, int]] = []
        for index, raw_text in enumerate(data.get("text", [])):
            word = str(raw_text).strip()
            if not word:
                continue
            try:
                confidence = float(data["conf"][index])
                height = int(data["height"][index])
            except (KeyError, ValueError, TypeError):
                continue
            if confidence < 0 or height <= 0:
                continue
            words.append((word, height))

        if len(words) < 3:
            return None

        heights = [height for _, height in words]
        median_height = statistics.median(heights)
        threshold = max(6, int(median_height * 0.72))
        small_words = [word for word, height in words if height <= threshold]
        if not small_words:
            return None
        return " ".join(small_words[:300])
