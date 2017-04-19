import gubed

gubed.autoload()

import time

@gubed.trace
def func(a=1, b=2):
    pass

def hello():
    func(7, 8)

print('app start')
func(5, 6)
hello()
gubed.autoload()
