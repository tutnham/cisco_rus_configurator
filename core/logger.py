"""
Logging configuration for Cisco Translator
"""

import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(log_level=logging.INFO, log_dir="logs"):
    """
    Setup application logging
    
    Args:
        log_level: Logging level (default: INFO)
        log_dir: Directory for log files
    """
    # Create logs directory
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    all_logs_file = os.path.join(log_dir, "cisco_translator.log")
    file_handler = logging.handlers.RotatingFileHandler(
        all_logs_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_logs_file = os.path.join(log_dir, "errors.log")
    error_handler = logging.handlers.RotatingFileHandler(
        error_logs_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # SSH session logs (separate file for command history)
    ssh_logger = logging.getLogger('ssh_session')
    ssh_logger.setLevel(logging.INFO)
    ssh_logger.propagate = False  # Don't propagate to root logger
    
    session_logs_file = os.path.join(log_dir, f"session_{datetime.now().strftime('%Y%m%d')}.log")
    session_handler = logging.handlers.RotatingFileHandler(
        session_logs_file,
        maxBytes=20*1024*1024,  # 20MB
        backupCount=10,
        encoding='utf-8'
    )
    
    session_formatter = logging.Formatter(
        '%(asctime)s - %(message)s'
    )
    session_handler.setFormatter(session_formatter)
    ssh_logger.addHandler(session_handler)
    
    # Application activity logger
    activity_logger = logging.getLogger('activity')
    activity_logger.setLevel(logging.INFO)
    activity_logger.propagate = False
    
    activity_logs_file = os.path.join(log_dir, "activity.log")
    activity_handler = logging.handlers.RotatingFileHandler(
        activity_logs_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    activity_handler.setFormatter(simple_formatter)
    activity_logger.addHandler(activity_handler)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("="*50)
    logger.info("Cisco Translator Application Started")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")
    logger.info(f"Log directory: {os.path.abspath(log_dir)}")
    logger.info("="*50)

def get_session_logger():
    """Get the SSH session logger"""
    return logging.getLogger('ssh_session')

def get_activity_logger():
    """Get the activity logger"""
    return logging.getLogger('activity')

def log_command_execution(command, result, execution_time=None, error=None):
    """
    Log command execution details
    
    Args:
        command: Executed command
        result: Command result
        execution_time: Time taken to execute (optional)
        error: Error message if command failed (optional)
    """
    session_logger = get_session_logger()
    
    if error:
        session_logger.error(f"COMMAND FAILED: {command}")
        session_logger.error(f"ERROR: {error}")
    else:
        time_info = f" (took {execution_time:.2f}s)" if execution_time else ""
        session_logger.info(f"COMMAND: {command}{time_info}")
        
        # Log result (truncated if too long)
        if result:
            result_lines = result.split('\n')
            if len(result_lines) > 50:
                session_logger.info(f"RESULT: {len(result_lines)} lines of output")
                session_logger.debug(f"FULL RESULT:\n{result}")
            else:
                session_logger.info(f"RESULT:\n{result}")

def log_connection_event(event_type, host, username=None, success=True, error=None):
    """
    Log connection events
    
    Args:
        event_type: Type of event (connect, disconnect, etc.)
        host: Target host
        username: Username (optional)
        success: Whether the event was successful
        error: Error message if failed (optional)
    """
    activity_logger = get_activity_logger()
    
    user_info = f" as {username}" if username else ""
    status = "SUCCESS" if success else "FAILED"
    
    message = f"{event_type.upper()}: {host}{user_info} - {status}"
    if error:
        message += f" - {error}"
        
    if success:
        activity_logger.info(message)
    else:
        activity_logger.error(message)

def log_macro_execution(macro_name, commands_count, success=True, error=None):
    """
    Log macro execution
    
    Args:
        macro_name: Name of the executed macro
        commands_count: Number of commands in the macro
        success: Whether execution was successful
        error: Error message if failed (optional)
    """
    activity_logger = get_activity_logger()
    
    status = "SUCCESS" if success else "FAILED"
    message = f"MACRO EXECUTION: {macro_name} ({commands_count} commands) - {status}"
    
    if error:
        message += f" - {error}"
        
    if success:
        activity_logger.info(message)
    else:
        activity_logger.error(message)

def log_security_event(event_type, details=None):
    """
    Log security-related events
    
    Args:
        event_type: Type of security event
        details: Additional details (optional)
    """
    activity_logger = get_activity_logger()
    
    message = f"SECURITY: {event_type}"
    if details:
        message += f" - {details}"
        
    activity_logger.warning(message)

def get_log_files_info():
    """
    Get information about log files
    
    Returns:
        dict: Information about existing log files
    """
    log_dir = "logs"
    log_files = {}
    
    if os.path.exists(log_dir):
        for filename in os.listdir(log_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(log_dir, filename)
                stat = os.stat(filepath)
                log_files[filename] = {
                    'path': filepath,
                    'size_mb': round(stat.st_size / (1024*1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                }
                
    return log_files

def cleanup_old_logs(days_to_keep=30):
    """
    Clean up old log files
    
    Args:
        days_to_keep: Number of days of logs to keep
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        return
        
    import time
    cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
    removed_count = 0
    
    logger = logging.getLogger(__name__)
    
    try:
        for filename in os.listdir(log_dir):
            if filename.endswith('.log') or filename.endswith('.log.1'):
                filepath = os.path.join(log_dir, filename)
                if os.path.getctime(filepath) < cutoff_time:
                    os.remove(filepath)
                    removed_count += 1
                    logger.info(f"Removed old log file: {filename}")
                    
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old log files")
            
    except Exception as e:
        logger.error(f"Failed to cleanup old logs: {e}")
