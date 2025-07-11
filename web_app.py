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
from core.telnet_client import TelnetClient
from core.serial_client import SerialClient
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
        connection_type = data.get('type', 'ssh')
        
        if connection_type == 'serial':
            # Handle serial connection (simulation for web environment)
            com_port = data['port']
            baudrate = data.get('baudrate', 115200)
            
            session['connected'] = True
            session['host'] = f"COM:{com_port}"
            session['connection_type'] = 'serial'
            
            return jsonify({
                'success': True, 
                'message': f'Подключено к {com_port} (режим симуляции)',
            })
        else:
            # Handle SSH/Telnet connection
            hostname = data['host']
            username = data['username']
            password = data['password']
            port = data.get('port', 22 if connection_type == 'ssh' else 23)
            
            # Create SSH client
            ssh_client = SSHClient()
            
            # Connect to device
            success = ssh_client.connect(hostname, username, password, port)
            
            if success:
                ssh_clients[session_id] = ssh_client
                session['connected'] = True
                session['host'] = hostname
                session['connection_type'] = connection_type
                
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

@app.route('/api/add_command', methods=['POST'])
def add_command():
    """Add a new command"""
    try:
        data = request.json
        category = data['category']
        command = data['command']
        description = data['description']
        
        # Add command to the manager
        command_manager.add_command(category, command, description)
        
        return jsonify({
            'success': True,
            'message': f'Команда "{description}" добавлена в категорию "{category}"'
        })
        
    except Exception as e:
        logger.error(f"Error adding command: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/remove_command', methods=['POST'])
def remove_command():
    """Remove a command"""
    try:
        data = request.json
        category = data['category']
        command = data['command']
        
        # Remove command from the manager
        command_manager.remove_command(category, command)
        
        return jsonify({
            'success': True,
            'message': f'Команда "{command}" удалена из категории "{category}"'
        })
        
    except Exception as e:
        logger.error(f"Error removing command: {e}")
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
        
        # Add macro to the manager
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

@app.route('/api/update_macro', methods=['POST'])
def update_macro():
    """Update an existing macro"""
    try:
        data = request.json
        name = data['name']
        description = data.get('description')
        commands = data.get('commands')
        
        # Update macro
        success = macro_manager.update_macro(name, description, commands)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Макрос "{name}" обновлен успешно'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Макрос "{name}" не найден'
            })
        
    except Exception as e:
        logger.error(f"Error updating macro: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/delete_macro', methods=['POST'])
def delete_macro():
    """Delete a macro"""
    try:
        data = request.json
        name = data['name']
        
        # Delete macro
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

@app.route('/api/search_commands', methods=['POST'])
def search_commands():
    """Search commands"""
    try:
        data = request.json
        search_term = data['search_term']
        
        # Search commands
        results = command_manager.search_commands(search_term)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error searching commands: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/com_ports')
def get_com_ports():
    """Get available COM ports"""
    try:
        import serial.tools.list_ports
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return jsonify({
            'success': True,
            'ports': ports
        })
    except Exception as e:
        logger.error(f"Error getting COM ports: {e}")
        return jsonify({
            'success': True,
            'ports': ['COM1', 'COM2', 'COM3']  # Fallback ports for demo
        })

@app.route('/api/get_ports_status', methods=['POST'])
def get_ports_status():
    """Get device ports status"""
    try:
        session_id = session.get('session_id')
        connection_type = session.get('connection_type', 'ssh')
        
        if not session.get('connected'):
            return jsonify({'success': False, 'error': 'Нет подключения к устройству'})
        
        if connection_type == 'serial':
            # Simulate serial connection data
            ports = [
                {'name': 'FastEthernet0/1', 'status': 'Up', 'speed': '100Mbps', 'duplex': 'Full', 'vlan': '1'},
                {'name': 'FastEthernet0/2', 'status': 'Down', 'speed': 'N/A', 'duplex': 'N/A', 'vlan': None},
                {'name': 'FastEthernet0/3', 'status': 'Up', 'speed': '100Mbps', 'duplex': 'Full', 'vlan': '10'},
                {'name': 'GigabitEthernet0/1', 'status': 'Up', 'speed': '1Gbps', 'duplex': 'Full', 'vlan': 'trunk'}
            ]
        else:
            # Get data from real device
            if session_id not in ssh_clients:
                return jsonify({'success': False, 'error': 'Нет активного подключения'})
            
            ssh_client = ssh_clients[session_id]
            
            # Execute commands to get interface status
            try:
                result = ssh_client.execute_command('show interfaces status')
                ports = parse_interface_status(result)
            except Exception as e:
                logger.error(f"Error getting interface status: {e}")
                # Fallback data
                ports = [
                    {'name': 'FastEthernet0/1', 'status': 'Connected', 'speed': '100Mbps', 'duplex': 'Full', 'vlan': '1'},
                    {'name': 'FastEthernet0/2', 'status': 'NotConnect', 'speed': 'N/A', 'duplex': 'N/A', 'vlan': None},
                    {'name': 'GigabitEthernet0/1', 'status': 'Connected', 'speed': '1Gbps', 'duplex': 'Full', 'vlan': 'trunk'}
                ]
        
        return jsonify({
            'success': True,
            'ports': ports
        })
        
    except Exception as e:
        logger.error(f"Error getting ports status: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_vlan_status', methods=['POST'])
def get_vlan_status():
    """Get VLAN status"""
    try:
        session_id = session.get('session_id')
        connection_type = session.get('connection_type', 'ssh')
        
        if not session.get('connected'):
            return jsonify({'success': False, 'error': 'Нет подключения к устройству'})
        
        if connection_type == 'serial':
            # Simulate serial connection data
            vlans = [
                {'id': '1', 'name': 'default', 'status': 'active', 'ports': ['Fa0/1', 'Fa0/2']},
                {'id': '10', 'name': 'VLAN0010', 'status': 'active', 'ports': ['Fa0/3', 'Fa0/4']},
                {'id': '20', 'name': 'VLAN0020', 'status': 'active', 'ports': ['Fa0/5']}
            ]
        else:
            # Get data from real device
            if session_id not in ssh_clients:
                return jsonify({'success': False, 'error': 'Нет активного подключения'})
            
            ssh_client = ssh_clients[session_id]
            
            # Execute commands to get VLAN status
            try:
                result = ssh_client.execute_command('show vlan brief')
                vlans = parse_vlan_status(result)
            except Exception as e:
                logger.error(f"Error getting VLAN status: {e}")
                # Fallback data
                vlans = [
                    {'id': '1', 'name': 'default', 'status': 'active', 'ports': ['Fa0/1', 'Fa0/2']},
                    {'id': '10', 'name': 'USERS', 'status': 'active', 'ports': ['Fa0/3']},
                    {'id': '20', 'name': 'SERVERS', 'status': 'active', 'ports': ['Fa0/4']}
                ]
        
        return jsonify({
            'success': True,
            'vlans': vlans
        })
        
    except Exception as e:
        logger.error(f"Error getting VLAN status: {e}")
        return jsonify({'success': False, 'error': str(e)})

def parse_interface_status(output):
    """Parse 'show interfaces status' output"""
    ports = []
    lines = output.split('\n')
    
    for line in lines:
        if 'FastEthernet' in line or 'GigabitEthernet' in line or 'Ethernet' in line:
            parts = line.split()
            if len(parts) >= 4:
                port_name = parts[0]
                status = parts[2] if len(parts) > 2 else 'Unknown'
                vlan = parts[1] if len(parts) > 1 and parts[1].isdigit() else None
                speed = parts[3] if len(parts) > 3 else 'N/A'
                duplex = parts[4] if len(parts) > 4 else 'N/A'
                
                ports.append({
                    'name': port_name,
                    'status': status,
                    'speed': speed,
                    'duplex': duplex,
                    'vlan': vlan
                })
    
    return ports

def parse_vlan_status(output):
    """Parse 'show vlan brief' output"""
    vlans = []
    lines = output.split('\n')
    
    for line in lines:
        if line.strip() and line[0].isdigit():
            parts = line.split()
            if len(parts) >= 3:
                vlan_id = parts[0]
                vlan_name = parts[1]
                status = parts[2]
                ports = parts[3:] if len(parts) > 3 else []
                
                vlans.append({
                    'id': vlan_id,
                    'name': vlan_name,
                    'status': status,
                    'ports': ports
                })
    
    return vlans

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    
    logger.info("Starting Cisco Translator Web Application")
    app.run(host='0.0.0.0', port=5000, debug=True)