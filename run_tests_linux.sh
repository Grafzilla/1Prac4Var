#!/bin/bash
echo "Тестирование эмулятора из bash-скрипта"
echo "Запуск с sample_vfs.csv и test_script_stage4.sh"
python3 shell_emulator.py --vfs sample_vfs.csv --script test_script_stage4.sh
echo "Запуск с другим VFS"
python3 shell_emulator.py --vfs sample_vfs.csv
