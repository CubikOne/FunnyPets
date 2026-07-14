# FunnyPets для Windows 10/11

Порт на Python + tkinter + WinAPI. Один файл, зависимостей нет —
хватает стандартного Python с [python.org](https://python.org).

## Запуск из исходников

```bat
python windows\funnypets_win.py
```

## Готовый exe

Собирается автоматически на GitHub Actions при каждом пуше:
**Actions → build-windows-exe → последний зелёный ран → артефакт
`FunnyPets-windows`**. Внутри один `FunnyPets.exe` — скачал и запустил.

Собрать самому (на Windows):

```bat
pip install pyinstaller
pyinstaller --onefile --noconsole --name FunnyPets --add-data "linux/sprites.json;." windows/funnypets_win.py
```

SmartScreen на неподписанный exe скажет «неизвестный издатель» —
«Подробнее → Выполнить в любом случае».

## Что умеет

Почти всё из macOS-версии: кот/хомяк (щёчки надуваются при печати),
5 окрасов + 4 узора, глаза за курсором, месит лапками при печати
(честная детекция клавиатуры через `GetAsyncKeyState` — без прав
администратора), перегрев от быстрой печати, мурчание от поглаживания,
сон при простое (ночью быстрее), **охота за курсором** (потряси мышкой),
**рулон бумаги при скролле**, прогулки, peek-режим (перетащи за край),
помодоро, разминка, имена, интеграция с Claude Code.

## Claude Code на Windows

Питомец читает `%USERPROFILE%\.comnyan\agent`. Hooks в
`~/.claude/settings.json` (если Claude Code работает через Git Bash,
команды те же, что на macOS/Linux):

```json
"hooks": {
  "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "mkdir -p ~/.comnyan && echo thinking > ~/.comnyan/agent"}]}],
  "Stop": [{"hooks": [{"type": "command", "command": "echo done > ~/.comnyan/agent"}]}]
}
```

## Ограничения

- Нет импорта окрасов (JSON/PNG), шапок и напоминаний по времени.
- Звуки — системные бипы.
- Скролл ловится низкоуровневым хуком мыши; если антивирус его
  заблокирует, всё остальное продолжит работать, исчезнет только рулон.
- Настройки: `%APPDATA%\FunnyPets\config.json`.
- Автозапуск: положи ярлык exe в `shell:startup` (Win+R).
