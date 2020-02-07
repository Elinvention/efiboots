import logging
import sys

import efibootmgr_gui


logging.basicConfig(level=0)

test = []
try:
	with open(sys.argv[1]) as f:
		test = f.readlines()
except:
	print("Specify a file with test data, like test/myinput.test", file=sys.stderr)
	sys.exit(-1)

print('#' * 20, 'TEST', '#' * 20)
for line in test:
	print(repr(line))
print('#' * 20, 'TEST', '#' * 20)
  
def run_efibootmgr_stub():
	logging.debug("efibootmgr stub called and returned test data")
	return test

efibootmgr_gui.run_efibootmgr = run_efibootmgr_stub
efibootmgr_gui.main()
