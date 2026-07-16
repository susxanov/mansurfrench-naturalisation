# Mansur French — Telegram Quiz Bot

Бот публикует Telegram Quiz по расписанию:

- понедельник–суббота;
- 5 вопросов в 09:00;
- 5 вопросов в 19:30;
- часовой пояс `Europe/Paris`;
- сначала официальные вопросы, затем mise en situation, затем bonus culture;
- PostgreSQL сохраняет позицию и историю публикаций.

## Файлы данных

Помести в папку `data/`:

```text
official_questions_258_audited.json
mise_en_situation_100.json
bonus_culture_60.json
```

## Команды администратора

- `/status` — состояние цикла;
- `/force 5` — немедленно отправить до 5 вопросов;
- `/reset_cycle` — начать новый цикл с первого официального вопроса.

## Railway Variables

```text
BOT_TOKEN
TELEGRAM_CHAT_ID
ADMIN_USER_ID
DATABASE_URL
TIMEZONE=Europe/Paris
MORNING_TIME=09:00
EVENING_TIME=19:30
QUESTIONS_PER_BLOCK=5
ACTIVE_COLLECTIONS=official,mise_en_situation,bonus_culture
CYCLE_MODE=loop
```

`TELEGRAM_CHAT_ID` может выглядеть как `-1001234567890` или как `@channel_username`.

## Развёртывание

1. Добавь эти файлы в корень GitHub-репозитория.
2. Убедись, что три JSON находятся в `data/`.
3. В Railway создай проект из GitHub-репозитория.
4. Добавь PostgreSQL.
5. Добавь переменные среды.
6. Railway запустит команду `python -m bot.main`.

## Проверка данных

```bash
python scripts/validate_data.py
```
