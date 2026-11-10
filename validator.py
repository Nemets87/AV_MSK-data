import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter

# ------------------------------------------------------------
# НАСТРОЙКИ
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
FEED_PATH = BASE_DIR / "feed.xml"
IMAGES_DIR = BASE_DIR / "public_images"

# Расширения, которые считаем изображениями
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".bmp"}


def ok(msg: str) -> None:
    print(f"✅ {msg}")


def warn(msg: str) -> None:
    print(f"⚠️  {msg}")


def fail(msg: str) -> None:
    print(f"❌ {msg}")
    sys.exit(1)


def is_image_reference(value: str) -> bool:
    """Проверяет, похоже ли значение на путь к изображению."""
    value_lower = value.lower()
    return any(ext in value_lower for ext in IMAGE_EXTENSIONS)


def normalize_path(value: str) -> str:
    """
    Приводит путь к имени файла.
    Например: 'images/photo.jpg' -> 'photo.jpg'.
    """
    return Path(value.strip().split("?")[0]).name


def collect_image_references(root: ET.Element) -> set[str]:
    """
    Собирает все упоминания изображений из XML:
    - из текстовых значений элементов;
    - из значений атрибутов.
    Возвращает множество имён файлов.
    """
    refs: set[str] = set()
    for elem in root.iter():
        # Атрибуты
        for attr_value in elem.attrib.values():
            if is_image_reference(attr_value):
                refs.add(normalize_path(attr_value))
        # Текстовое содержимое
        if elem.text and is_image_reference(elem.text):
            refs.add(normalize_path(elem.text))
    return refs


def main() -> None:
    print("🔍 Запуск валидатора AV_MSK-data\n")

    # 1. Проверка существования фида
    if not FEED_PATH.exists():
        fail(f"Файл фида не найден: {FEED_PATH}")
    if FEED_PATH.stat().st_size == 0:
        fail(f"Файл фида пустой: {FEED_PATH}")
    ok(f"Файл фида найден: {FEED_PATH.name} ({FEED_PATH.stat().st_size:,} байт)")

    # 2. Парсинг XML
    try:
        tree = ET.parse(FEED_PATH)
        root = tree.getroot()
    except ET.ParseError as e:
        fail(f"Ошибка парсинга XML: {e}")
    ok("XML успешно распарсен")

    # 3. Статистика по тегам
    tag_counter = Counter(elem.tag for elem in root.iter())
    total_elements = sum(tag_counter.values())
    print(f"\n📊 Всего элементов в XML: {total_elements:,}")
    print("   Топ-5 тегов:")
    for tag, count in tag_counter.most_common(5):
        print(f"   - <{tag}>: {count:,}")

    # 4. Сбор ссылок на изображения из XML
    xml_refs = collect_image_references(root)
    print(f"\n🖼️  Упоминаний изображений в XML: {len(xml_refs)}")

    # 5. Проверка папки с изображениями
    if not IMAGES_DIR.exists():
        fail(f"Папка с изображениями не найдена: {IMAGES_DIR}")
    disk_files = {
        f.name for f in IMAGES_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    }
    ok(f"Файлов изображений на диске: {len(disk_files)}")

    # 6. Сравнение множеств
    missing_on_disk = xml_refs - disk_files
    unused_on_disk = disk_files - xml_refs

    if missing_on_disk:
        warn(f"В XML упомянуты, но отсутствуют на диске: {len(missing_on_disk)}")
        for name in sorted(missing_on_disk)[:10]:
            print(f"   - {name}")
        if len(missing_on_disk) > 10:
            print(f"   ... и ещё {len(missing_on_disk) - 10}")
    else:
        ok("Все изображения из XML присутствуют на диске")

    if unused_on_disk:
        warn(f"На диске есть, но не упомянуты в XML: {len(unused_on_disk)}")
        for name in sorted(unused_on_disk)[:10]:
            print(f"   - {name}")
        if len(unused_on_disk) > 10:
            print(f"   ... и ещё {len(unused_on_disk) - 10}")
    else:
        ok("Нет «сиротских» изображений — все файлы упомянуты в XML")

    # 7. Итог
    if missing_on_disk:
        print("\n❌ Валидация завершена с ошибками: часть изображений отсутствует.")
        sys.exit(1)

    print("\n🎉 Валидация пройдена успешно!")


if __name__ == "__main__":
    main()
