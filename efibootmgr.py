import subprocess
import sys

def find_esp():
	custom_efi = [ arg.split("--efi=")[1] for arg in sys.argv[1:] if arg.startswith("--efi=") ]
	if len(custom_efi) > 0:
		res = custom_efi[0]
	else:	
		# findmnt --noheadings --output SOURCE --target /boot/efi
		cmd = ["findmnt", "--noheadings", "--output", "SOURCE", "--target", "/boot/efi"]
		print(*cmd)
		try:
			res = subprocess.check_output(cmd).decode('UTF-8').strip()
		except subprocess.CalledProcessError as e:
			print("Please mount ESP to /boot/efi", sep='\n', file=sys.stderr)
			return
	print(res)
	return res[:-1], res[-1:]

ESP_DISK, ESP_PART = find_esp()
ESP = ("--disk", ESP_DISK, "--part", ESP_PART)

def set_boot_next(num):
	if num is None:
		cmd = ["pkexec", "efibootmgr", *ESP, "--delete-bootnext"]
	else:
		cmd = ["pkexec", "efibootmgr", *ESP, "--bootnext", num]
	print(*cmd)
	return subprocess.check_output(cmd)

def set_boot_order(order):
	cmd = ["pkexec", "efibootmgr", *ESP, "--bootorder", ','.join(order)]
	print(*cmd)
	return subprocess.check_output(cmd)

def remove(num):
	cmd = ["pkexec", "efibootmgr", *ESP, "--delete-bootnum", "--bootnum", num]
	print(*cmd)
	return subprocess.check_output(cmd)

def add(label, loader):
	cmd = ["pkexec", "efibootmgr", *ESP, "--create", "--label", label, "--loader", loader]
	print(*cmd)
	return subprocess.check_output(cmd)

def active(num):
	cmd = ["pkexec", "efibootmgr", *ESP, "--bootnum", num, "--active"]
	print(*cmd)
	return subprocess.check_output(cmd)

def inactive(num):
	cmd = ["pkexec", "efibootmgr", *ESP, "--bootnum", num, "--inactive"]
	print(*cmd)
	return subprocess.check_output(cmd)

def output():
	try:
		return subprocess.check_output([ "efibootmgr", "-v" ]).decode('UTF-8').strip().split('\n')
	except subprocess.CalledProcessError as e:
		print(e, file=sys.stderr)

