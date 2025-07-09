-- Инициализация базы данных PostgreSQL для Cisco Translator
-- Выполните этот скрипт после создания базы данных

-- Подключение к базе данных cisco_translator
\c cisco_translator;

-- Таблица для хранения команд
CREATE TABLE IF NOT EXISTS commands (
    id SERIAL PRIMARY KEY,
    command TEXT NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для хранения макросов
CREATE TABLE IF NOT EXISTS macros (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    author VARCHAR(100) DEFAULT 'user',
    created_date DATE DEFAULT CURRENT_DATE,
    modified_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для команд в макросах
CREATE TABLE IF NOT EXISTS macro_commands (
    id SERIAL PRIMARY KEY,
    macro_id INTEGER REFERENCES macros(id) ON DELETE CASCADE,
    command TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для истории подключений
CREATE TABLE IF NOT EXISTS connection_history (
    id SERIAL PRIMARY KEY,
    host VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    connection_type VARCHAR(20) NOT NULL,
    port INTEGER,
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    disconnected_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'connected'
);

-- Таблица для истории команд
CREATE TABLE IF NOT EXISTS command_history (
    id SERIAL PRIMARY KEY,
    connection_id INTEGER REFERENCES connection_history(id),
    command TEXT NOT NULL,
    description TEXT,
    result TEXT,
    execution_time FLOAT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE
);

-- Таблица для настроек приложения
CREATE TABLE IF NOT EXISTS app_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_commands_category ON commands(category);
CREATE INDEX IF NOT EXISTS idx_command_history_connection ON command_history(connection_id);
CREATE INDEX IF NOT EXISTS idx_command_history_executed_at ON command_history(executed_at);
CREATE INDEX IF NOT EXISTS idx_connection_history_host ON connection_history(host);

-- Вставка базовых команд
INSERT INTO commands (command, description, category) VALUES
-- Show команды
('show version', 'Показать версию ПО и информацию об устройстве', 'show_commands'),
('show running-config', 'Показать текущую конфигурацию', 'show_commands'),
('show ip interface brief', 'Показать краткую информацию об IP интерфейсах', 'show_commands'),
('show interfaces', 'Показать состояние всех интерфейсов', 'show_commands'),
('show ip route', 'Показать таблицу маршрутизации', 'show_commands'),
('show arp', 'Показать ARP таблицу', 'show_commands'),
('show mac address-table', 'Показать таблицу MAC адресов', 'show_commands'),
('show vlan', 'Показать информацию о VLAN', 'show_commands'),

-- Настройка интерфейсов
('configure terminal', 'Войти в режим глобальной конфигурации', 'interface_config'),
('interface GigabitEthernet0/0', 'Войти в настройку интерфейса GigabitEthernet0/0', 'interface_config'),
('ip address 192.168.1.1 255.255.255.0', 'Назначить IP адрес интерфейсу', 'interface_config'),
('no shutdown', 'Включить интерфейс', 'interface_config'),
('shutdown', 'Выключить интерфейс', 'interface_config'),

-- Маршрутизация
('ip route 0.0.0.0 0.0.0.0 192.168.1.1', 'Добавить маршрут по умолчанию', 'routing'),
('router ospf 1', 'Настроить OSPF процесс 1', 'routing'),
('show ip protocols', 'Показать протоколы маршрутизации', 'routing'),

-- Безопасность
('username admin privilege 15 secret cisco123', 'Создать пользователя admin с привилегиями', 'security'),
('enable secret cisco123', 'Установить пароль привилегированного режима', 'security'),
('service password-encryption', 'Включить шифрование паролей', 'security'),

-- Диагностика
('ping 8.8.8.8', 'Проверить связность с 8.8.8.8', 'diagnostics'),
('traceroute 8.8.8.8', 'Проследить маршрут до 8.8.8.8', 'diagnostics'),
('show logging', 'Показать системные логи', 'diagnostics'),

-- Управление устройством
('copy running-config startup-config', 'Сохранить конфигурацию', 'device_management'),
('reload', 'Перезагрузить устройство', 'device_management'),
('show flash', 'Показать содержимое flash памяти', 'device_management');

-- Вставка базовых макросов
INSERT INTO macros (name, display_name, description, author) VALUES
('basic_info', 'Базовая информация', 'Получить основную информацию об устройстве', 'system'),
('interface_status', 'Статус интерфейсов', 'Проверить состояние всех интерфейсов', 'system'),
('routing_info', 'Информация о маршрутизации', 'Получить информацию о маршрутизации', 'system'),
('security_check', 'Проверка безопасности', 'Проверить настройки безопасности', 'system'),
('save_config', 'Сохранить конфигурацию', 'Сохранить текущую конфигурацию', 'system');

-- Команды для макросов
INSERT INTO macro_commands (macro_id, command, order_index) VALUES
-- basic_info макрос
(1, 'show version', 1),
(1, 'show ip interface brief', 2),
(1, 'show running-config | include hostname', 3),

-- interface_status макрос
(2, 'show interfaces', 1),
(2, 'show ip interface brief', 2),
(2, 'show interfaces status', 3),

-- routing_info макрос
(3, 'show ip route', 1),
(3, 'show ip protocols', 2),
(3, 'show arp', 3),

-- security_check макрос
(4, 'show running-config | include username', 1),
(4, 'show running-config | include enable', 2),
(4, 'show running-config | include access-list', 3),
(4, 'show line', 4),

-- save_config макрос
(5, 'copy running-config startup-config', 1);

-- Базовые настройки приложения
INSERT INTO app_settings (setting_key, setting_value) VALUES
('theme', 'light'),
('auto_save_layout', 'true'),
('connection_timeout', '10'),
('command_timeout', '30'),
('log_level', 'INFO'),
('enable_session_logging', 'true');

COMMIT;