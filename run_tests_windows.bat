@echo off
echo ������������ ��������� �� batch-�������
echo ������ � sample_vfs.csv � test_script_stage4.sh
python shell_emulator.py --vfs sample_vfs.csv --script test_script_stage4.sh
echo ������ � ������ VFS
python shell_emulator.py --vfs sample_vfs.csv
pause
