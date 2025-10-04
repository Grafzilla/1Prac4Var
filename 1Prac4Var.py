#!/usr/bin/env python
import sys
import os
import base64
import csv
import argparse
import subprocess
from io import StringIO
from datetime import datetime


# =========================== ЭТАП 1: REPL ===========================

# Класс VFS управляет виртуальной файловой системой, загруженной из CSV-файла.
class VFS:
    def __init__(self, vfs_path):
        # Проверка существования файла VFS
        if not os.path.exists(vfs_path):
            raise FileNotFoundError(f"VFS file not found: {vfs_path}")

        self.root = {}
        self.current_path = []
        self.load_vfs(vfs_path)

    def load_vfs(self, vfs_path):
        with open(vfs_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row_num, row in enumerate(reader, start=1):
                if len(row) < 3:
                    raise ValueError(f"Invalid VFS format in row {row_num}: {row}")
                path, file_type, data = row[0], row[1], row[2]

                # Проверка корректности типа файла
                if file_type not in ['dir', 'file']:
                    raise ValueError(f"Invalid file type '{file_type}' in row {row_num}")

                self.add_entry(path, file_type, data)

    def add_entry(self, path, file_type, data):
        parts = path.strip('/').split('/')
        current = self.root
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        name = parts[-1]
        if file_type == 'dir':
            if name not in current:
                current[name] = {}
        elif file_type == 'file':
            try:
                current[name] = base64.b64decode(data).decode('utf-8', errors='ignore')
            except:
                current[name] = data  # Если не base64, сохраняем как есть

    def get_current_dir(self):
        current = self.root
        for part in self.current_path:
            if part in current:
                current = current[part]
            else:
                return {}
        return current

    def change_dir(self, path):
        if path == '..':
            if self.current_path:
                self.current_path.pop()
            return True
        elif path == '.':
            return True
        elif path == '/':
            self.current_path = []
            return True

        # Обработка относительных путей
        if not path.startswith('/'):
            target_path = self.current_path[:]
            for part in path.split('/'):
                if part == '..':
                    if target_path:
                        target_path.pop()
                elif part and part != '.':
                    target_path.append(part)
        else:
            target_path = [p for p in path.split('/') if p]

        # Проверка существования пути
        current = self.root
        try:
            for part in target_path:
                if part not in current or not isinstance(current[part], dict):
                    return False
                current = current[part]
            self.current_path = target_path
            return True
        except:
            return False

    def list_dir(self):
        current = self.get_current_dir()
        return list(current.keys())

    def get_full_path(self):
        if not self.current_path:
            return '/'
        return '/' + '/'.join(self.current_path)


# Класс ShellEmulator реализует логику командной строки.
class ShellEmulator:
    def __init__(self, vfs_path=None, script_path=None):
        self.vfs = VFS(vfs_path) if vfs_path else None
        self.script_path = script_path
        self.running = True
        self.commands = {
            'ls': 'List directory contents',
            'cd': 'Change directory',
            'pwd': 'Print working directory',
            'whoami': 'Print current user',
            'tree': 'Display directory tree',
            'history': 'Show command history',
            'head': 'Show first lines of a file',
            'tail': 'Show last lines of a file',
            'help': 'Show this help message',
            'exit': 'Exit the emulator',
            'touch': 'Create or update a file timestamp'
        }
        self.command_history = []

    def show_help(self):
        help_text = "Available commands:\n"
        for cmd, desc in sorted(self.commands.items()):
            help_text += f"  {cmd:<10} - {desc}\n"
        return help_text.strip()

    def parse_command(self, line):
        # Парсер команд, поддерживающий аргументы в кавычках
        tokens = []
        current = ''
        in_quotes = False
        i = 0
        while i < len(line):
            char = line[i]
            if char == '"' and not in_quotes:
                in_quotes = True
            elif char == '"' and in_quotes:
                in_quotes = False
            elif char == ' ' and not in_quotes:
                if current:
                    tokens.append(current)
                    current = ''
            else:
                current += char
            i += 1
        if current:
            tokens.append(current)
        return tokens

    def execute_command(self, command, args):
        # Добавляем команду в историю
        self.command_history.append(f"{command} {' '.join(args)}")

        if command == 'exit':
            self.running = False
            return "exit"
        elif command == 'help':
            return self.show_help()
        elif command == 'ls':
            if self.vfs:
                files = self.vfs.list_dir()
                return '\n'.join(files) if files else ""
            else:
                return "ls: no vfs loaded"
        elif command == 'cd':
            if not args:
                # cd без аргументов переходит в корень
                if self.vfs:
                    self.vfs.current_path = []
                    return ""
                else:
                    return "cd: no vfs loaded"

            if self.vfs:
                if self.vfs.change_dir(args[0]):
                    return ""
                else:
                    return f"cd: {args[0]}: No such file or directory"
            else:
                return "cd: no vfs loaded"
        elif command == 'pwd':
            if self.vfs:
                return self.vfs.get_full_path()
            else:
                return "/"
        elif command == 'whoami':
            return os.getenv('USER', 'user')
        elif command == 'tree':
            if self.vfs:
                return self._tree_dir(self.vfs.get_current_dir(), '', True)
            else:
                return "tree: no vfs loaded"
        elif command == 'history':
            return "\n".join([f"{i + 1}: {cmd}" for i, cmd in enumerate(self.command_history)])
        elif command == 'head' or command == 'tail':
            if not args:
                return f"{command}: missing file argument"
            file_path = args[0]
            n_lines = int(args[1]) if len(args) > 1 else 10
            return self._process_head_tail(file_path, n_lines, command)
        elif command == 'touch':
            if not args:
                return "touch: missing file operand"
            file_path = args[0]
            return self._touch_file(file_path)
        else:
            return f"{command}: command not found\nType 'help' to see available commands"

    def _tree_dir(self, directory, prefix, is_last):
        result = ""
        items = sorted(list(directory.keys()))
        for i, item in enumerate(items):
            is_last_item = i == len(items) - 1
            result += prefix + ("└── " if is_last_item else "├── ") + item + "\n"
            if isinstance(directory[item], dict):
                extension = "    " if is_last_item else "│   "
                result += self._tree_dir(directory[item], prefix + extension, is_last_item)
        return result.rstrip()

    def _process_head_tail(self, file_path, n_lines, command):
        parts = file_path.strip('/').split('/')
        current = self.vfs.root
        for part in parts[:-1]:
            if part in current:
                current = current[part]
            else:
                return f"{command}: {file_path}: No such file"
        file_name = parts[-1]
        if file_name not in current or isinstance(current[file_name], dict):
            return f"{command}: {file_path}: Not a file"
        content = current[file_name].split('\n')
        if command == 'head':
            return '\n'.join(content[:n_lines])
        return '\n'.join(content[-n_lines:])

    # =========================== ЭТАП 5: Дополнительные команды ===========================

    def _touch_file(self, file_path):
        """
        Реализация команды touch:
        - Если файл существует, обновляет его содержимое (в данном случае — пустое).
        - Если файл не существует, создаёт новый пустой файл.
        """
        if not self.vfs:
            return "touch: no vfs loaded"

        # Разбиваем путь на компоненты
        parts = file_path.strip('/').split('/')
        current = self.vfs.root
        for part in parts[:-1]:
            if part in current and isinstance(current[part], dict):
                current = current[part]
            else:
                return f"touch: {file_path}: No such directory"

        file_name = parts[-1]
        # Если файл уже существует и это файл (а не папка)
        if file_name in current and not isinstance(current[file_name], dict):
            current[file_name] = ""  # Обновляем содержимое файла (делаем его пустым)
        # Если файл не существует, создаём его
        elif file_name not in current:
            current[file_name] = ""
        # Если это директория, то ошибка
        else:
            return f"touch: {file_path}: Is a directory"

        return ""

    # =========================== ОСТАЛЬНАЯ ЛОГИКА ===========================

    def run_script(self, script_path):
        if not os.path.exists(script_path):
            print(f"Script not found: {script_path}")
            return
        with open(script_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                print(f"$ {line}")
                tokens = self.parse_command(line)
                if not tokens:
                    continue
                result = self.execute_command(tokens[0], tokens[1:])
                if result and result != "exit":
                    print(result)
                elif result == "exit":
                    break

    def run_repl(self):
        print("Shell Emulator v1.0")
        print("Message of the Day: Welcome to the shell emulator!")
        print("Type 'help' to see available commands, 'exit' to quit")
        print()
        while self.running:
            if self.vfs:
                prompt = f"user@emulator:{self.vfs.get_full_path()}$ "
            else:
                prompt = "user@emulator:$ "
            try:
                line = input(prompt).strip()
            except (EOFError, KeyboardInterrupt):
                print("\nexit")
                break
            if not line:
                continue
            tokens = self.parse_command(line)
            if not tokens:
                continue
            result = self.execute_command(tokens[0], tokens[1:])
            if result and result != "exit":
                print(result)
            elif result == "exit":
                break


def create_sample_vfs():
    """Создает пример VFS файла для тестирования"""
    sample_data = [
        ["/", "dir", ""],
        ["/home", "dir", ""],
        ["/home/user", "dir", ""],
        ["/home/user/documents", "dir", ""],
        ["/home/user/documents/file1.txt", "file", base64.b64encode(
            b"Hello World\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nLine 8\nLine 9\nLine 10\nLine 11\nLine 12").decode()],
        ["/home/user/documents/file2.txt", "file", base64.b64encode(
            b"Test content\nLine A\nLine B\nLine C\nLine D\nLine E\nLine F\nLine G\nLine H\nLine I\nLine J\nLine K").decode()],
        ["/var", "dir", ""],
        ["/var/log", "dir", ""],
        ["/var/log/system.log", "file", base64.b64encode(
            b"System log content\nLog entry 1\nLog entry 2\nLog entry 3\nLog entry 4\nLog entry 5\nLog entry 6\nLog entry 7\nLog entry 8\nLog entry 9\nLog entry 10\nLog entry 11").decode()],
        ["/etc", "dir", ""],
        ["/etc/config.txt", "file", base64.b64encode(
            b"Configuration file\nSetting1=Value1\nSetting2=Value2\nSetting3=Value3\nSetting4=Value4\nSetting5=Value5\nSetting6=Value6\nSetting7=Value7\nSetting8=Value8\nSetting9=Value9\nSetting10=Value10\nSetting11=Value11").decode()]
    ]
    with open("sample_vfs.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(sample_data)

    # Создаем тестовый скрипт для текущего этапа (включая touch)
    script_content = """# Тестовый скрипт для эмулятора этапа 5
help
pwd
ls
cd /home/user
pwd
ls
cd documents
pwd
ls
cd ../../..
pwd
tree
history
head file1.txt 5
tail file2.txt 3
ls /nonexistent
cd /nonexistent
head /nonexistent_file.txt
touch newfile.txt
ls
touch file1.txt
ls -l
"""
    with open("test_script_stage5.sh", "w") as f:
        f.write(script_content)


def create_os_scripts():
    """Создает скрипты реальной ОС для тестирования"""

    # Bash-скрипт для Linux/Mac
    bash_script_content = """#!/bin/bash
echo "Тестирование эмулятора из bash-скрипта"
echo "Запуск с sample_vfs.csv и test_script_stage5.sh"
python3 shell_emulator.py --vfs sample_vfs.csv --script test_script_stage5.sh
echo "Запуск с другим VFS"
python3 shell_emulator.py --vfs sample_vfs.csv
"""
    with open("run_tests_linux.sh", "w") as f:
        f.write(bash_script_content)
    os.chmod("run_tests_linux.sh", 0o755)  # Делаем исполняемым

    # Batch-скрипт для Windows
    batch_script_content = """@echo off
echo Тестирование эмулятора из batch-скрипта
echo Запуск с sample_vfs.csv и test_script_stage5.sh
python shell_emulator.py --vfs sample_vfs.csv --script test_script_stage5.sh
echo Запуск с другим VFS
python shell_emulator.py --vfs sample_vfs.csv
pause
"""
    with open("run_tests_windows.bat", "w") as f:
        f.write(batch_script_content)


def main():
    parser = argparse.ArgumentParser(description="Shell Emulator")
    parser.add_argument("--vfs", help="Path to VFS CSV file")
    parser.add_argument("--script", help="Path to startup script")
    parser.add_argument("--create-sample", action="store_true", help="Create sample VFS and script files")

    args = parser.parse_args()

    if args.create_sample:
        create_sample_vfs()
        create_os_scripts()
        print("Created sample_vfs.csv, test_script_stage5.sh, run_tests_linux.sh, run_tests_windows.bat")
        return

    if args.vfs and not os.path.exists(args.vfs):
        print(f"VFS file not found: {args.vfs}")
        return

    # Обработка ошибок загрузки VFS
    try:
        emulator = ShellEmulator(args.vfs, args.script)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading VFS: {e}")
        return

    if args.script:
        emulator.run_script(args.script)

    emulator.run_repl()

if __name__ == "__main__":
    main()