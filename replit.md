# Cisco Translator - System Architecture Documentation

## Overview

Cisco Translator is a desktop application designed to facilitate the use of Cisco CLI commands through a user-friendly interface with Russian translation. The application serves as a bridge between Russian-speaking users (primarily students and junior network engineers) and Cisco network devices, providing translated command descriptions and secure device connectivity options.

The application is built using Python with Tkinter for the GUI framework, supporting multiple connection methods including SSH, Telnet, and COM port connections to Cisco devices.

## System Architecture

### Frontend Architecture
- **GUI Framework**: Tkinter with ttk widgets for modern styling
- **Architecture Pattern**: MVC-like separation with dedicated GUI modules
- **Components**:
  - `MainWindow`: Primary application interface
  - `ConnectionDialog`: Device connection configuration
  - `ThemeManager`: UI theming and styling system
- **Styling**: Custom theme system supporting light/dark modes with configurable color schemes

### Backend Architecture
- **Core Modules**: Modular design with specialized managers for different functionalities
- **Command Processing**: JSON-based command database with Russian translations
- **Connection Management**: Multi-protocol support (SSH/Telnet/COM) with secure credential handling
- **Macro System**: Predefined command sequences for common administrative tasks

### Key Components

#### Connection Management
- **SSHClient**: Paramiko-based SSH connectivity with session management
- **Security Module**: Encrypted credential storage using Fernet symmetric encryption
- **Connection Types**: SSH (port 22), Telnet (port 23), and COM port support
- **Session Handling**: Automatic session timeout and cleanup

#### Command System
- **CommandManager**: JSON-based command database with categorized Cisco CLI commands
- **Russian Translation**: Full command descriptions in Russian for accessibility
- **Command Categories**: Organized by function (show commands, interface config, routing, etc.)
- **Command Validation**: Built-in safety checks for destructive operations

#### Macro Management
- **MacroManager**: Predefined command sequences for common tasks
- **Macro Types**: Basic info gathering, security checks, configuration backup
- **Extensibility**: JSON-based macro definitions allowing custom macro creation

#### Security Features
- **Encrypted Storage**: Fernet encryption for stored credentials
- **Session Security**: Configurable session timeouts and automatic cleanup
- **Safe Defaults**: Confirmation prompts for potentially destructive commands
- **Key Management**: Secure master key generation and storage

#### Logging System
- **Structured Logging**: Rotating file logs with configurable retention
- **Session Logging**: Optional command session recording
- **Log Categories**: Application logs, connection logs, and session logs
- **Debug Support**: Configurable debug logging for troubleshooting

## Data Flow

1. **Application Startup**: 
   - Load configuration from `config/settings.json`
   - Initialize logging system
   - Load command database and macros from JSON files

2. **Device Connection**:
   - User configures connection through ConnectionDialog
   - Credentials encrypted and optionally stored
   - SSH/Telnet client establishes secure connection
   - Connection status updated in main interface

3. **Command Execution**:
   - User selects command from Russian-translated list
   - Application maps to corresponding English CLI command
   - Command sent to device through established connection
   - Response captured and displayed in output panel

4. **Session Management**:
   - Commands logged to session history
   - Optional session recording to file
   - Automatic session cleanup on disconnect

## External Dependencies

### Core Libraries
- **paramiko**: SSH client functionality for secure device connections
- **cryptography**: Encryption/decryption for secure credential storage
- **tkinter**: Built-in Python GUI framework (no external dependency)

### System Requirements
- **Python 3.7+**: Core runtime requirement
- **Operating System**: Cross-platform (Windows, Linux, macOS)
- **Network Access**: Required for device connectivity

### Device Compatibility
- **Cisco IOS**: Primary target platform
- **SSH/Telnet**: Standard network protocols
- **Serial Console**: COM port support for direct device access

## Deployment Strategy

### Packaging
- **Standalone Application**: Python script with dependency management
- **Configuration**: JSON-based settings with secure credential storage
- **Data Files**: Embedded command database and macro definitions

### File Structure
```
cisco_translator/
├── main.py                 # Application entry point
├── config/
│   ├── settings.json       # Application configuration
│   └── secure_storage.dat  # Encrypted credential storage
├── data/
│   ├── commands.json       # Command database with translations
│   └── macros.json         # Predefined command macros
├── core/                   # Core business logic
├── gui/                    # User interface components
└── logs/                   # Application and session logs
```

### Security Considerations
- **Credential Encryption**: All stored passwords encrypted with Fernet
- **File Permissions**: Restrictive permissions on key files (0o600)
- **Session Security**: Configurable timeouts and automatic cleanup
- **Network Security**: Secure protocols (SSH) preferred over Telnet

### Configuration Management
- **JSON Configuration**: Human-readable settings in `config/settings.json`
- **Runtime Configuration**: Dynamic settings modification without restart
- **Default Fallbacks**: Graceful handling of missing configuration files

## Changelog

```
Changelog:
- July 08, 2025. Initial setup
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```