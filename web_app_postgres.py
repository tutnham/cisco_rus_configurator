#!/usr/bin/env python3
"""
Cisco Translator Web Application with PostgreSQL support
"""

from flask import Flask, render_template, request, jsonify, session
import logging
import time
from datetime import datetime

# Import our core modules
from core.logger import setup_logging
from core.config_manager import ConfigManager
from core.database import DatabaseManager, PostgreSQLCommandManager, PostgreSQLMacroManager, PostgreSQLHistoryManager
from core.ssh_client import SSHClient

app = Flask(__name__)
app.secret_key = 'cisco_translator_postgres_secret_key_2025'

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global managers
config_manager = ConfigManager()
db_manager = None
command_manager = None
macro_manager = None
history_manager = None
ssh_clients = {}  # Store SSH clients by session ID

def initialize_database():
    """Initialize database connection and managers"""
    global db_manager, command_manager, macro_manager, history_manager
    
    try:
        db_config = config_manager.get_database_config()
        db_manager = DatabaseManager(db_config)
        
        command_manager = PostgreSQLCommandManager(db_manager)
        macro_manager = PostgreSQLMacroManager(db_manager)
        history_manager = PostgreSQLHistoryManager(db_manager)
        
        logger.info("PostgreSQL managers initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")
        return False

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/categories')
def get_categories():
    """Get command categories"""
    try:
        categories = command_manager.get_categories()
        return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/commands/<category>')
def get_commands(category):
    """Get commands for a category"""
    try:
        commands = command_manager.get_commands_by_category(category)
        return jsonify({'success': True, 'commands': commands})
    except Exception as e:
        logger.error(f"Error getting commands: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/macros')
def get_macros():
    """Get all macros"""
    try:
        macros = macro_manager.get_all_macros()
        return jsonify({'success': True, 'macros': macros})
    except Exception as e:
        logger.error(f"Error getting macros: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/connect', methods=['POST'])
def connect():
    """Connect to device"""
    try:
        data = request.json
        session_id = session.get('session_id', str(time.time()))
        session['session_id'] = session_id
        
        hostname = data['host']
        username = data['username']
        password = data['password']
        port = data.get('port', 22)
        connection_type = data.get('type', 'ssh')
        
        # Create SSH client
        ssh_client = SSHClient()
        
        # Connect to device
        success = ssh_client.connect(hostname, username, password, port)
        
        if success:
            ssh_clients[session_id] = ssh_client
            session['connected'] = True
            session['host'] = hostname
            session['connection_type'] = connection_type
            
            # Log connection to database
            connection_id = history_manager.log_connection(hostname, username, connection_type, port)
            session['connection_id'] = connection_id
            
            return jsonify({
                'success': True, 
                'message': f'Подключено к {hostname} через {connection_type.upper()}'
            })
        else:
            return jsonify({'success': False, 'error': 'Не удалось подключиться к устройству'})
            
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from device"""
    try:
        session_id = session.get('session_id')
        connection_id = session.get('connection_id')
        
        if session_id in ssh_clients:
            ssh_clients[session_id].disconnect()
            del ssh_clients[session_id]
        
        if connection_id:
            history_manager.log_disconnection(connection_id)
        
        session['connected'] = False
        session['host'] = None
        session['connection_id'] = None
        
        return jsonify({'success': True, 'message': 'Отключено от устройства'})
        
    except Exception as e:
        logger.error(f"Disconnect error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/execute', methods=['POST'])
def execute_command():
    """Execute a command"""
    try:
        data = request.json
        session_id = session.get('session_id')
        connection_id = session.get('connection_id')
        
        if not session.get('connected') or session_id not in ssh_clients:
            return jsonify({'success': False, 'error': 'Нет подключения к устройству'})
        
        ssh_client = ssh_clients[session_id]
        command = data['command']
        description = data.get('description', command)
        
        # Execute command
        start_time = time.time()
        result = ssh_client.execute_command(command)
        execution_time = time.time() - start_time
        
        # Log command execution to database
        if connection_id:
            history_manager.log_command_execution(
                connection_id, command, description, result, execution_time, True
            )
        
        return jsonify({
            'success': True,
            'command': command,
            'result': result,
            'execution_time': round(execution_time, 2),
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        
        # Log failed command execution
        connection_id = session.get('connection_id')
        if connection_id:
            history_manager.log_command_execution(
                connection_id, data.get('command', ''), 
                data.get('description', ''), str(e), None, False
            )
        
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/execute_macro', methods=['POST'])
def execute_macro():
    """Execute a macro"""
    try:
        data = request.json
        session_id = session.get('session_id')
        connection_id = session.get('connection_id')
        
        if not session.get('connected') or session_id not in ssh_clients:
            return jsonify({'success': False, 'error': 'Нет подключения к устройству'})
        
        ssh_client = ssh_clients[session_id]
        macro_name = data['macro_name']
        
        # Get macro from database
        macro = macro_manager.get_macro(macro_name)
        if not macro:
            return jsonify({'success': False, 'error': f'Макрос "{macro_name}" не найден'})
        
        results = []
        for command in macro['commands']:
            try:
                start_time = time.time()
                result = ssh_client.execute_command(command)
                execution_time = time.time() - start_time
                
                # Log command execution
                if connection_id:
                    history_manager.log_command_execution(
                        connection_id, command, f"Макрос: {macro_name}", 
                        result, execution_time, True
                    )
                
                results.append({
                    'command': command,
                    'result': result,
                    'execution_time': round(execution_time, 2),
                    'success': True
                })
            except Exception as e:
                # Log failed command execution
                if connection_id:
                    history_manager.log_command_execution(
                        connection_id, command, f"Макрос: {macro_name}", 
                        str(e), None, False
                    )
                
                results.append({
                    'command': command,
                    'result': str(e),
                    'success': False
                })
        
        return jsonify({
            'success': True,
            'macro_name': macro_name,
            'results': results,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
    except Exception as e:
        logger.error(f"Macro execution error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/add_command', methods=['POST'])
def add_command():
    """Add a new command"""
    try:
        data = request.json
        category = data['category']
        command = data['command']
        description = data['description']
        
        # Add command to database
        command_manager.add_command(category, command, description)
        
        return jsonify({
            'success': True,
            'message': f'Команда "{description}" добавлена в категорию "{category}"'
        })
        
    except Exception as e:
        logger.error(f"Error adding command: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/add_macro', methods=['POST'])
def add_macro():
    """Add a new macro"""
    try:
        data = request.json
        name = data['name']
        description = data['description']
        commands = data['commands']
        author = data.get('author', 'user')
        
        # Add macro to database
        success = macro_manager.create_macro(name, description, commands, author)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Макрос "{name}" создан успешно'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Макрос с именем "{name}" уже существует'
            })
        
    except Exception as e:
        logger.error(f"Error adding macro: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/delete_macro', methods=['POST'])
def delete_macro():
    """Delete a macro"""
    try:
        data = request.json
        name = data['name']
        
        # Delete macro from database
        success = macro_manager.delete_macro(name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Макрос "{name}" удален успешно'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Макрос "{name}" не найден'
            })
        
    except Exception as e:
        logger.error(f"Error deleting macro: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/command_history')
def get_command_history():
    """Get command execution history"""
    try:
        limit = request.args.get('limit', 100, type=int)
        history = history_manager.get_command_history(limit)
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        logger.error(f"Error getting command history: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status')
def get_status():
    """Get connection status"""
    return jsonify({
        'connected': session.get('connected', False),
        'host': session.get('host'),
        'session_id': session.get('session_id'),
        'database_connected': db_manager is not None
    })

if __name__ == '__main__':
    # Initialize database
    if not initialize_database():
        print("Ошибка: Не удалось подключиться к PostgreSQL")
        print("Проверьте настройки в config/database.json")
        exit(1)
    
    logger.info("Starting Cisco Translator Web Application with PostgreSQL")
    app.run(host='0.0.0.0', port=5000, debug=True)