#!/usr/bin/expect



set timeout -1
spawn git pull
match_max 100000
expect -exact "Username for 'https://github.com': "
send -- "SuperSmay\r"
expect -exact "SuperSmay\r
Password for 'https://SuperSmay@github.com': "
send -- "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\r"
expect eof



spawn $env(SHELL)
send "source Elliot/bin/activate\r"
send "python3.9 /home/smay/Documents/ElliotBot/main.py\r"

expect eof
