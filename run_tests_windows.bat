@echo off
echo Тестирование эмулятора из batch-скрипта
echo Запуск с sample_vfs.csv и test_script_stage4.sh
python shell_emulator.py --vfs sample_vfs.csv --script test_script_stage4.sh
echo Запуск с другим VFS
python shell_emulator.py --vfs sample_vfs.csv
pause
