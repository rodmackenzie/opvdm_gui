#    Organic Photovoltaic Device Model - a drift diffusion base/Shockley-Read-Hall
#    model for organic solar cells. 
#    Copyright (C) 2012 Roderick C. I. MacKenzie
#
#	roderick.mackenzie@nottingham.ac.uk
#	www.opvdm.com
#	Room B86 Coates, University Park, Nottingham, NG7 2RD, UK
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License v2.0, as published by
#    the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import sys
import os
import shutil
from win_lin import running_on_linux
if running_on_linux()==False:
	import _winreg

phys_path=None
light_dll_path=None
exe_command=None
win_install_path=None
install_path=None

def cal_install_path():
	global install_path
	if running_on_linux()==True:
		install_path="/usr/share/opvdm/"
	else:
		try:
			registry_key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Software\\opvdm", 0, _winreg.KEY_READ)
			value, regtype = _winreg.QueryValueEx(registry_key, "installpath")
			_winreg.CloseKey(registry_key)
			print "Install path at", value
			install_path=value
		except WindowsError:
			print "No registry key found using default"
			install_path="c:\\opvdm"

def calculate_paths():
	global install_path
	global phys_path
	global exe_command


	cal_install_path()

	phys_path=os.path.join(os.getcwd(),"phys")
	if os.path.isdir(phys_path)==False:
		phys_path=os.path.join(install_path,"phys")

	if running_on_linux() == True:
		if os.path.isfile("./go.o")==True:
			exe_command=os.path.join(os.getcwd(), "go.o")
		elif os.path.isfile("./main.c")==True:
			exe_command=os.path.join(os.getcwd(), "go.o")
		else:
			exe_command="opvdm_core"

	else:
		if os.path.isfile("opvdm_core.exe")==True:
			exe_command=os.path.join(os.getcwd(), "opvdm_core.exe")
		else:
			exe_command=os.path.join(install_path,"opvdm_core.exe")

	global light_dll_path
	local=os.path.join(os.getcwd(),"light")
	if os.path.isfile(local):
		light_dll_path=local
	else:
		if running_on_linux()==True:
			light_dll_path="/usr/lib64/opvdm/"
		else:
			light_dll_path=os.path.join(install_path,"light")


def get_install_path():
	global install_path
	return install_path

def get_phys_path():
	global phys_path
	return phys_path

def get_light_dll_path():
	global light_dll_path
	return light_dll_path

def get_exe_command():
	global exe_command
	return exe_command

def get_exe_name():
	if running_on_linux() == True:
		if os.path.isfile("./go.o")==True:
			exe_name="go.o"
		elif os.path.isfile("./main.c")==True:
			exe_name="go.o"
		else:
			exe_name="opvdm_core"
		return exe_name
	else:
		if os.path.isfile("opvdm_core.exe")==True:
			exe_name="opvdm_core.exe"
		else:
			exe_name="opvdm_core.exe"
		return exe_name

def get_inp_file_path():
	global install_path
	if running_on_linux() == True:
		if os.path.isfile("opvdm.py")==True:
			path=os.getcwd()
		else:
			path="/usr/share/opvdm/"
		return path
	else:
		if os.path.isfile("opvdm.py")==True:
			path=os.path.join(os.getcwd(), "\\")
		else:
			path=install_path
		return path

def get_icon_file_path():
	global install_path
	if running_on_linux() == True:
		if os.path.isfile("main.c")==True:
			path=os.path.join(os.getcwd(),"gui")
		else:
			path="/usr/share/opvdm/gui/"
		return path
	else:
		if os.path.isfile("opvdm.py")==True:
			path=os.path.join(os.getcwd(), "\\")
		else:
			path=os.path.join(install_path,"gui")
		return path

def find_data_file(name):

	local_file=os.path.join(os.getcwd(),name)
	if os.path.isfile("main.c")==True:
		ret=local_file
	else:
		ret=os.path.join(get_inp_file_path(),name)
	return ret

