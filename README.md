Бро, отличная идея. Сделаем два артефакта: **README.md** (красивый, понятный, для студентов и рекрутёров) и **скрипт-валидатор** на Python, который проверяет целостность фида и картинок. Плюс бонус — GitHub Actions, чтобы проверка запускалась при каждом обновлении данных.

---

## 📄 1. `README.md` для репозитория `AV_MSK-data`

Скопируй этот текст в файл `README.md` в корне репозитория.

```markdown
# AV_MSK-data

Публичный датасет с регулярно обновляемым XML-фидом и набором изображений.
Проект создан как учебный полигон для отработки навыков **валидации данных**, **парсинга XML** и **CI/CD** в контексте автоматизации тестирования.

## 📦 Структура

```
AV_MSK-data/
├── feed.xml            # Основной фид с данными (обновляется автоматически)
├── public_images/      # Изображения, привязанные к записям фида
└── README.md           # Этот файл
```

- **`feed.xml`** — структурированный XML-файл с записями. Содержит текстовые поля, ссылки и пути к изображениям.
- **`public_images/`** — папка с публичными изображениями (JPG, PNG и т.п.), которые используются в фиде.

## 🎯 Назначение

Репозиторий демонстрирует типовой сценарий работы с данными в продакшене:
1. Источник данных регулярно обновляет фид.
2. Автоматизация проверяет, что структура не сломалась и все связи «запись → изображение» целы.
3. CI запускает валидацию при каждом пуше, чтобы не пропустить регресс.

Это отличное упражнение для начинающих AQA: учит работать с XML, файловой системой, писать проверки и интегрировать их в GitHub Actions.

## 🚀 Как использовать

### Клонировать репозиторий

```bash
git clone https://github.com/Nemets87/AV_MSK-data.git
cd AV_MSK-data
```

### Запустить валидатор локально

```bash
python validator.py
```

Скрипт проверит:
- существует ли `feed.xml` и не пустой ли он;
- корректно ли парсится XML;
- все ли пути к изображениям из фида существуют в `public_images/`;
- нет ли «сиротских» картинок, не упомянутых в фиде;
- выведет статистику по тегам и изображениям.

Если всё хорошо — код выхода `0`. Если найдены проблемы — `1` и понятное сообщение.

### Запустить через CI

Проверка настроена в `.github/workflows/validate.yml` и запускается:
- при каждом пуше в `main`;
- по расписанию (ежедневно).

Результат виден на вкладке **Actions**.

## 🧠 Что внутри валидатора

- Парсинг XML через стандартную библиотеку `xml.etree.ElementTree`.
- Сбор всех ссылок на изображения из текстовых полей и атрибутов.
- Нормализация путей (берём только имя файла) — устойчиво к разным префиксам.
- Сравнение множеств: `ссылки в XML` ↔ `файлы на диске`.
- Подробный вывод статистики: количество элементов, тегов, изображений.

Скрипт легко адаптировать под конкретную схему фида: достаточно уточнить, по каким тегам искать изображения, если структура изменится.

## 🛠️ Технологии

- Python 3.11+
- `xml.etree.ElementTree` (встроенный)
- GitHub Actions (CI)

## 👤 Автор

Сергей Федоров ([@Nemets87](https://github.com/Nemets87))  
Проект используется в учебных целях и как пример портфолио для позиции AQA.
```

---

## 🐍 2. Скрипт-валидатор `validator.py`

Создай файл `validator.py` в корне репозитория. Скрипт универсален, но учитывает типичные сценарии.

```python
r"""
Валидатор данных для репозитория AV_MSK-data.

Проверяет:
  1. Существование и непустоту feed.xml.
  2. Корректность парсинга XML.
  3. Что все изображения, упомянутые в XML, существуют в public_images/.
  4. Что все файлы из public_images/ упомянуты в XML (нет «сиротских» картинок).
  5. Выводит статистику по тегам и изображениям.

Запуск:
  python validator.py
Возвращает код 0 при успехе, 1 при ошибках.
"""

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
```

---

## ⚙️ 3. GitHub Actions: `.github/workflows/validate.yml`

Добавь этот файл, чтобы валидатор запускался при каждом пуше и ежедневно.

```yaml
name: Validate Data

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  schedule:
    - cron: '0 6 * * *'   # каждый день в 6:00 UTC
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run validator
        run: python validator.py

      - name: Upload validation report (if failed)
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: validation-report
          path: |
            feed.xml
            public_images/
          retention-days: 3
```

> 💡 **Зачем артефакт при ошибке?** Если CI упадёт, ты сможешь скачать текущее состояние фида и картинок и разобраться локально.

---

## 🎓 Как это объяснить студентам (короткий сценарий урока)

1. **Проблема:** данные обновляются каждый день, а мы не хотим, чтобы в продакшен уехал битый фид или «потерялись» картинки.
2. **Решение:** пишем валидатор — маленькую программу-сторожа.
3. **Что проверяет сторож:**
   - Файл на месте и не пустой.
   - XML парсится (нет битых тегов).
   - Каждая картинка из фида реально лежит в папке.
   - Нет лишних картинок, которые никто не использует.
4. **Как автоматизировать:** GitHub Actions запускает сторожа при каждом пуше. Если что-то не так — красный крестик и понятное сообщение.
5. **Чему учимся:** парсинг XML, работа с файловой системой, множества в Python, CI/CD, написание понятных ошибок.

---

## 💎 Как усилить резюме

Добавь в раздел проектов:

> **AV_MSK-data** — публичный датасет с XML-фидом и изображениями.  
> Разработал Python-валидатор структуры фида и целостности связей «запись → изображение». Настроил CI-проверку в GitHub Actions (запуск при пушах и по расписанию).  
> [github.com/Nemets87/AV_MSK-data](https://github.com/Nemets87/AV_MSK-data)

Это покажет рекрутёру, что ты умеешь не только писать тесты, но и **работать с данными, автоматизировать проверки и внедрять CI**.

Готово, бро! Можешь коммитить README, `validator.py` и workflow. Если структура `feed.xml` окажется нестандартной и валидатор что-то не найдёт — просто покажи фрагмент XML, и мы за минуту адаптируем логику. 💪🚀
