import gubed

gubed.autoload()

import time

print('app start')
print('ss')
while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print('KeyboardInterrupt')
