#!/bin/bash
echo "������������ ��������� �� bash-�������"
echo "������ � sample_vfs.csv � test_script_stage4.sh"
python3 shell_emulator.py --vfs sample_vfs.csv --script test_script_stage4.sh
echo "������ � ������ VFS"
python3 shell_emulator.py --vfs sample_vfs.csv
