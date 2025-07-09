#!/usr/bin/env python3
"""
Cisco Translator Web Application
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json
import os
import logging
from datetime import datetime
import threading
import time

# Import our core modules
from core.command_manager import CommandManager
from core.macro_manager import MacroManager
from core.ssh_client import SSHClient
from core.security import SecureStorage
from core.logger import setup_logging

app = Flask(__name__)
app.secret_key = 'cisco_translator_secret_key_2025'

# Global managers
command_manager = CommandManager()
macro_manager = MacroManager()
secure_storage = SecureStorage()
ssh_clients = {}  # Store SSH clients by session ID

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

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
        
        # Create SSH client
        ssh_client = SSHClient()
        
        # Connect to device
        success = ssh_client.connect(
            data['host'],
            data['username'],
            data['password'],
            data.get('port', 22)
        )
        
        if success:
            ssh_clients[session_id] = ssh_client
            session['connected'] = True
            session['host'] = data['host']
            return jsonify({'success': True, 'message': f'Успешно подключено к {data["host"]}'})
        else:
            return jsonify({'success': False, 'error': 'Не удалось подключиться'})
            
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from device"""
    try:
        session_id = session.get('session_id')
        if session_id in ssh_clients:
            ssh_clients[session_id].disconnect()
            del ssh_clients[session_id]
        
        session['connected'] = False
        session['host'] = None
        
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
        
        if not session.get('connected') or session_id not in ssh_clients:
            return jsonify({'success': False, 'error': 'Нет подключения к устройству'})
        
        ssh_client = ssh_clients[session_id]
        command = data['command']
        
        # Execute command
        result = ssh_client.execute_command(command)
        
        return jsonify({
            'success': True,
            'command': command,
            'result': result,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/execute_macro', methods=['POST'])
def execute_macro():
    """Execute a macro"""
    try:
        data = request.json
        session_id = session.get('session_id')
        
        if not session.get('connected') or session_id not in ssh_clients:
            return jsonify({'success': False, 'error': 'Нет подключения к устройству'})
        
        ssh_client = ssh_clients[session_id]
        macro_name = data['macro_name']
        
        # Get macro
        macro = macro_manager.get_macro(macro_name)
        if not macro:
            return jsonify({'success': False, 'error': f'Макрос "{macro_name}" не найден'})
        
        results = []
        for command in macro['commands']:
            try:
                result = ssh_client.execute_command(command)
                results.append({
                    'command': command,
                    'result': result,
                    'success': True
                })
            except Exception as e:
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

@app.route('/api/status')
def get_status():
    """Get connection status"""
    return jsonify({
        'connected': session.get('connected', False),
        'host': session.get('host'),
        'session_id': session.get('session_id')
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    
    logger.info("Starting Cisco Translator Web Application")
    app.run(host='0.0.0.0', port=5000, debug=True)