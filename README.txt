1.
user@emulator:/$ help
Available commands:
  cd         - Change directory
  exit       - Exit the emulator
  head       - Show first lines of a file
  help       - Show this help message
  history    - Show command history
  ls         - List directory contents
  pwd        - Print working directory
  tail       - Show last lines of a file
  tree       - Display directory tree
  whoami     - Print current user
  touch      - Create or update a file timestamp


2. 
user@emulator:/$ ls
etc
home
var
user@emulator:/$ cd home
user@emulator:/home$ ls
user
user@emulator:/home$ cd user
user@emulator:/home/user$ ls
documents
user@emulator:/home/user$ cd documents
user@emulator:/home/user/documents$ ls
file1.txt
file2.txt

3.
user@emulator:/$ pwd
/
user@emulator:/$ cd home/user
user@emulator:/home/user$ pwd
/home/user
user@emulator:/home/user$ cd ..
user@emulator:/home$ pwd
/home
user@emulator:/home$ cd /var/log
user@emulator:/var/log$ pwd
/var/log

4.
user@emulator:/$ pwd
/
user@emulator:/$ cd etc
user@emulator:/etc$ pwd
/etc

5.
user@emulator:/$ whoami
user

6.
user@emulator:/$ tree
├── etc
│   └── config.txt
├── home
│   └── user
│       └── documents
│           ├── file1.txt
│           └── file2.txt
└── var
    └── log
        └── system.log

7.
user@emulator:/$ ls
etc home var
user@emulator:/$ pwd
/
user@emulator:/$ history
1: ls
2: pwd

8.
user@emulator:/home/user/documents$ head file1.txt 3
Hello World
Line 2
Line 3
user@emulator:/home/user/documents$ head file2.txt
Test content
Line A
Line B
Line C
Line D
Line E
Line F
Line G
Line H
Line I

9.
user@emulator:/home/user/documents$ tail file1.txt 2
Line 11
Line 12
user@emulator:/home/user/documents$ tail /var/log/system.log 4
Log entry 8
Log entry 9
Log entry 10
Log entry 11

10.
user@emulator:/$ exit
exit
C:\Users\denis\Desktop\git\1Prac4Var>

11.
$ touch newfile.txt
$ ls
newfile.txt


------------ПРИМЕРЫ ОШИБОК------------

1. Несуществующая команда

user@emulator:/$ nonexistent_command
nonexistent_command: command not found
Type 'help' to see available commands

2. Несуществующая директория

user@emulator:/$ cd /nonexistent
cd: /nonexistent: No such file or directory

3. head от несуществующего файла

user@emulator:/$ head nonexistent_file.txt
head: nonexistent_file.txt: No such file

4. head от директории

user@emulator:/$ head home
head: home: Not a file