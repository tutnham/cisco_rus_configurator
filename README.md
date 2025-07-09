🛠 Инструкция по подключению к PostgreSQL и запуску Cisco Translator

## Содержание

- [Подготовка PostgreSQL](#подготовка-postgresql)
- [Настройка подключения к БД](#настройка-подключения-к-бд)
- [Модификация кода для PostgreSQL](#модификация-кода-для-postgresql)
- [Запуск GUI приложения](#запуск-gui-приложения)
- [Запуск веб-приложения](#запуск-веб-приложения)
- [Устранение неполадок](#устранение-неполадок)
- [Резервное копирование и восстановление](#резервное-копирование-и-восстановление)
- [Мониторинг и логирование](#мониторинг-и-логирование)

---

## Подготовка PostgreSQL

### 1. Установка PostgreSQL

#### Windows:

- Скачайте с официального сайта:  
  [PostgreSQL Download (Windows)](https://www.postgresql.org/download/windows/)
- Или используйте пакетные менеджеры:

```powershell
# Chocolatey
choco install postgresql

# Scoop
scoop install postgresql
```

#### Linux (Ubuntu/Debian):

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib python3-dev libpq-dev
```

#### macOS:

```bash
# Homebrew
brew install postgresql
```

---

### 2. Запуск службы PostgreSQL

#### Windows (в командной строке от администратора):

```cmd
net start postgresql-x64-14
```

#### Linux:

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### macOS:

```bash
brew services start postgresql
```

---

### 3. Создание базы данных и пользователя

#### Войдите в `psql`:

```bash
# Linux
sudo -u postgres psql

# Windows
psql -U postgres
```

#### Выполните команды:

```sql
-- Создание базы данных
CREATE DATABASE cisco_translator;

-- Создание пользователя
CREATE USER cisco_user WITH PASSWORD 'cisco_password_2025';

-- Предоставление прав
GRANT ALL PRIVILEGES ON DATABASE cisco_translator TO cisco_user;

-- Выход
\q
```

---

### 4. Создание таблиц

Создайте файл `database/init_postgres.sql`, затем выполните:

```bash
psql -U postgres -d cisco_translator -f database/init_postgres.sql
```

Пример содержимого SQL-файла:
```
supabase/migrations/20250709083505_throbbing_brook.sql
core/database.py
config/database.json
requirements.txt
core/config_manager.py
main_postgres.py
web_app_postgres.py
```

---

## Настройка подключения к БД

### 1. Выполнение SQL скрипта инициализации

```bash
psql -U postgres -d cisco_translator -f database/init_postgres.sql
```

### 2. Установка зависимостей Python

```bash
pip install -r requirements.txt
# или по отдельности:
pip install psycopg2-binary paramiko cryptography pyserial flask python-dotenv
```

### 3. Настройка файла конфигурации

Файл: `config/database.json`

```json
{
  "postgresql": {
    "host": "localhost",
    "port": 5432,
    "database": "cisco_translator",
    "user": "cisco_user",
    "password": "ваш_пароль_здесь"
  }
}
```

---

## Модификация кода для PostgreSQL

Основные изменения уже внесены в следующие файлы:

- `core/database.py` — работа с БД
- `core/config_manager.py` — управление настройками
- `main_postgres.py` — GUI версия
- `web_app_postgres.py` — веб-версия

---

## Запуск GUI приложения

### 1. Подготовка к запуску

```bash
# Проверка состояния PostgreSQL
sudo systemctl status postgresql  # Linux
net start postgresql-x64-14       # Windows

# Проверка подключения
psql -U cisco_user -d cisco_translator -c "SELECT COUNT(*) FROM commands;"
```

### 2. Запуск приложения

```bash
python main_postgres.py
# или обычная версия:
python main.py
```

### 3. Возможные проблемы и решения

- **Ошибка подключения к PostgreSQL**

```bash
sudo systemctl restart postgresql
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

- **Ошибка аутентификации**

```sql
sudo -u postgres psql
ALTER USER cisco_user WITH PASSWORD 'новый_пароль';
```

---

## Запуск веб-приложения

### 1. Запуск сервера

```bash
python web_app_postgres.py
# или обычная версия:
python web_app.py
```

### 2. Доступ через браузер

Откройте:  
👉 http://localhost:5000

### 3. Функционал

- Подключение: SSH/Telnet/COM порт
- Выполнение команд: выбор из категорий
- Макросы: создание, редактирование, удаление
- История команд
- Мониторинг устройств: порты, VLAN

---

## Установка на разных ОС

### Windows

```powershell
# Установка Python: https://www.python.org/downloads/
pip install -r requirements.txt
python main_postgres.py
```

### Linux (Ubuntu/Debian)

```bash
sudo apt install python3 python3-pip postgresql postgresql-contrib python3-dev libpq-dev
pip3 install -r requirements.txt
python3 main_postgres.py
```

### macOS

```bash
# Установка Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install postgresql
brew services start postgresql
pip3 install -r requirements.txt
python3 main_postgres.py
```

---

## Устранение неполадок

### Проблемы с PostgreSQL

```bash
# Linux
sudo systemctl status postgresql
sudo journalctl -u postgresql

# Windows
net start postgresql-x64-14

# Конфигурационные файлы
sudo nano /etc/postgresql/14/main/postgresql.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

### Проблемы с Python

```bash
pip install psycopg2-binary paramiko cryptography
```

- **tkinter не найден**:

```bash
sudo apt install python3-tk  # Linux
```

### Проблемы с веб-приложением

```bash
# Найдите занятый порт
lsof -i :5000
kill -9 PID
```

---

## Резервное копирование и восстановление

### Создание резервной копии

```bash
pg_dump -U cisco_user -h localhost cisco_translator > backup_$(date +%Y%m%d).sql
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/
```

### Восстановление

```bash
psql -U cisco_user -h localhost cisco_translator < backup_20250101.sql
tar -xzf config_backup_20250101.tar.gz
```

---

## Мониторинг и логирование

### Логи приложения

```bash
tail -f logs/cisco_translator.log
tail -f logs/session_$(date +%Y%m%d).log
tail -f logs/errors.log
```

### PostgreSQL мониторинг

```bash
# Активные подключения
psql -U postgres -c "SELECT * FROM pg_stat_activity WHERE datname = 'cisco_translator';"

# Размер базы данных
psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('cisco_translator'));"
```
