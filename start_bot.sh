### BEGIN INIT INFO
# Provides:          start_bot.sh
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start daemon at boot time
# Description:       Enable service provided by daemon.
### END INIT INFO

#!/bin/sh
cd /home/pi/code
python3.7 /home/pi/code/bot.py
