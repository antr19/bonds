# ==========================================
# 1. Builder Stage: Компиляция в бинарный файл (Nuitka)
# ==========================================
FROM python:3.14-rc-slim AS builder

WORKDIR /app

# Устанавливаем C-компилятор (gcc), patchelf и заголовочные файлы для Nuitka
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ccache \
    patchelf \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry и Nuitka
RUN pip3 install --no-cache-dir poetry nuitka

# Копируем конфиги и устанавливаем зависимости проекта
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main --no-interaction --no-ansi

# Копируем исходный код приложения
COPY . /app

# Компилируем Python-проект в один бинарный файл (директория main.dist)
# --standalone: собирает приложение со всеми зависимостями
# --mode=onefile: упаковывает все в единственный бинарник
RUN python -m nuitka \
    --standalone \
    --onefile \
    --lto=no \
    --assume-yes-for-downloads \
    --output-filename=moex.bin \
    main.py

# ==========================================
# 2. Runner Stage: Минимальный бинарный контейнер
# ==========================================
FROM debian:trixie-slim AS runner

WORKDIR /app

# Создаем не-root пользователя для безопасности
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Копируем ТОЛЬКО скомпилированный бинарный файл из этапа builder
COPY --from=builder /app/moex.bin /app/moex.bin
COPY --from=builder /app/config.yml /app/config.yml

# Настраиваем права доступа
RUN chown -R appuser:appgroup /app
USER appuser

# Запуск чистого скомпилированного бинарника
CMD ["/app/moex.bin"]