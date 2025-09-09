# FROM python:3.13-slim
#
# WORKDIR /app
#
# COPY pyproject.toml pdm.lock README.md ./
#
# RUN pip install pdm && \
#     pdm sync
#
# COPY . .
#
# WORKDIR /app/src
#
# CMD ["pdm", "run", "python", "-m", "app"]

# FROM python:3.13-slim
#
# WORKDIR /app
#
# RUN mkdir -p src/logger/log_files
#
# COPY pyproject.toml pdm.lock README.md ./
#
# RUN pip install pdm && \
#     pdm sync --production
#
# COPY . .
#
# RUN mkdir -p src/logger/log_files
#
# WORKDIR /app/src
#
# CMD ["pdm", "run", "python", "-m", "app"]

FROM python:3.13-slim

WORKDIR /app

RUN mkdir -p src/logger/log_files

COPY pyproject.toml pdm.lock README.md ./

RUN pip install pdm && \
    pdm sync --production

COPY . .

RUN mkdir -p src/logger/log_files

# Запускаем из корня с указанием пути
CMD ["pdm", "run", "python", "-m", "src.app"]