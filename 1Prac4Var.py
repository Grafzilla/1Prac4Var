import sys
import os
import base64
import csv
import argparse
from io import StringIO


class VFS:
    def __init__(self, vfs_path):
        self.root = {}
        self.current_path = []
        self.load_vfs(vfs_path)

    def load_vfs(self, vfs_path):
        with open(vfs_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 3:
                    continue
                path, file_type, data = row[0], row[1], row[2]
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
            'touch': 'Create empty file (not implemented)',
            'help': 'Show this help message',
            'exit': 'Exit the emulator'
        }

    def show_help(self):
        help_text = "Available commands:\n"
        for cmd, desc in sorted(self.commands.items()):
            help_text += f"  {cmd:<10} - {desc}\n"
        return help_text.strip()

    def parse_command(self, line):
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
        elif command == 'touch':
            return "touch: not implemented in memory-only mode"
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
        ["/home/user/documents/file1.txt", "file", base64.b64encode(b"Hello World").decode()],
        ["/home/user/documents/file2.txt", "file", base64.b64encode(b"Test content").decode()],
        ["/var", "dir", ""],
        ["/var/log", "dir", ""],
        ["/var/log/system.log", "file", base64.b64encode(b"System log content").decode()],
        ["/etc", "dir", ""],
        ["/etc/config.txt", "file", base64.b64encode(b"Configuration file").decode()]
    ]

    with open("sample_vfs.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(sample_data)

    # Создаем тестовый скрипт
    script_content = """# Тестовый скрипт для эмулятора
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
"""

    with open("test_script.sh", "w") as f:
        f.write(script_content)


def main():
    parser = argparse.ArgumentParser(description="Shell Emulator")
    parser.add_argument("--vfs", help="Path to VFS CSV file")
    parser.add_argument("--script", help="Path to startup script")
    parser.add_argument("--create-sample", action="store_true", help="Create sample VFS and script files")

    args = parser.parse_args()

    if args.create_sample:
        create_sample_vfs()
        print("Created sample_vfs.csv and test_script.sh")
        return

    if args.vfs and not os.path.exists(args.vfs):
        print(f"VFS file not found: {args.vfs}")
        return

    emulator = ShellEmulator(args.vfs, args.script)

    if args.script:
        emulator.run_script(args.script)

    emulator.run_repl()


if __name__ == "__main__":
    main()