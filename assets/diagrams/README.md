# Диаграммы Mavix (для ВКР)

Чёрно-белые диаграммы в стиле ВКР (Times New Roman / Liberation Serif,
ортогональные связи). Исходники — `*.svg` (+ генераторы `gen_*.py`),
готовые картинки — `png/*.png`.

## Перегенерация PNG
Нужен PySide6 (есть в venv MavixDesktop-UI) и Liberation Serif.
```bash
export LD_LIBRARY_PATH=/path/to/gl/libs   # для offscreen Qt при необходимости
python svg2png.py <input.svg> png/<out.png> 2.0
```
`svg2png.py` рендерит SVG через QtSvg в PNG (масштаб 2× = чёткость для печати).
