import pygtk
pygtk.require('2.0')
import gc
import gtk
import sys
import os
import shutil
from inp import inp_update_token_value
from inp import inp_get_token_value
from search import return_file_list
from plot import plot_data
from plot import plot_info
from plot import check_info_file
from util import find_data_file
from about import about_dialog_show
from used_files_menu import used_files_menu
from server import server
from plot_dlg import plot_dlg_class
from plot_gen import plot_gen
from plot_command import plot_command_class
import threading
import gobject
import pyinotify
import multiprocessing
import time
import glob
from scan_select import select_param
from config import config

class scan_vbox(gtk.VBox):

	icon_theme = gtk.icon_theme_get_default()

	def rename(self,new_name):
		self.sim_name=new_name
		whole_path=os.getcwd()+'/'+self.sim_name
		self.sim_dir=whole_path+'/'
		self.status_bar.push(self.context_id, self.sim_dir)
		self.set_tab_caption(os.path.basename(new_name))
		#self.tab_label.set_text(os.path.basename(new_name))
		self.reload_liststore()
		self.plotted_graphs.init(self.sim_dir+'opvdm_last_menu.inp',self.callback_last_menu_click)
		self.plotted_graphs.reload_list()
		

	def callback_move_down(self, widget, data=None):

		selection = self.treeview.get_selection()
		model, iter = selection.get_selected()

		if iter:
			path = model.get_path(iter)[0]
 			self.liststore_combobox.move_after( iter,self.liststore_combobox.iter_next(iter))
			#self.liststore_combobox.swap(path+1,path)
	def add_line(self,data):
		selection = self.treeview.get_selection()
		model, iter = selection.get_selected()

		if iter:
			path = model.get_path(iter)[0]
			self.liststore_combobox.insert(path+1,data)
		else:
			self.liststore_combobox.append(data)
		self.save_combo()
		self.rebuild_liststore_op_type()

	def callback_add_item(self, widget, data=None):
		self.add_line(["Select parameter", "0.0 0.0", "scan"])
		

	def callback_copy_item(self, widget, data=None):
		selection = self.treeview.get_selection()
		model, iter = selection.get_selected()

		if iter:
			build=model[0][0]+"\n"+model[0][1]+"\n"+model[0][2]
			self.clipboard.set_text(build, -1)

	def callback_paste_item(self, widget, data=None):
		selection = self.treeview.get_selection()
		model, iter = selection.get_selected()

		if iter:
			text = self.clipboard.wait_for_text()
			if text != None:
				array=text.rstrip().split('\n')
				self.add_line(array)
				#build=model[0][0]+"\n"+model[0][1]+"\n"+model[0][2]
				#self.clipboard.set_text(build, -1)
	def callback_show_list(self, widget, data=None):
		self.select_param_window.select_window.show()

	def callback_delete_item(self, widget, data=None):
		#self.liststore_combobox.append(["Television", "Samsung"])

		selection = self.treeview.get_selection()
		model, iter = selection.get_selected()

		if iter:
			path = model.get_path(iter)[0]
			model.remove(iter)
			self.save_combo()

		self.rebuild_liststore_op_type()

	def apply_constant(self):
		for i in range(0, len(self.liststore_combobox)):
			if self.liststore_combobox[i][2]=="constant":
				pos_mirror_dest=self.combo_box_list.index(self.liststore_combobox[i][0])
				inp_update_token_value(self.param_list[pos_mirror_dest].filename, self.param_list[pos_mirror_dest].token, self.liststore_combobox[i][1])
				print os.getcwd()
				print "Replace",self.param_list[pos_mirror_dest].filename,self.param_list[pos_mirror_dest].token,self.liststore_combobox[i][1]

	def apply_mirror(self):
		for i in range(0, len(self.liststore_combobox)):
			for ii in range(0, len(self.liststore_combobox)):
				if self.liststore_combobox[i][2]==self.liststore_combobox[ii][0]:
					#I have found two matching IDs
					pos_mirror_src=self.combo_box_list.index(self.liststore_combobox[i][2])
					pos_mirror_dest=self.combo_box_list.index(self.liststore_combobox[i][0])
					src_value=inp_get_token_value(self.param_list[pos_mirror_src].filename, self.param_list[pos_mirror_src].token)
					#pull out of the file the value
					if self.liststore_combobox[i][1]!="mirror":
						#find value in list
						orig_list=self.liststore_combobox[i][1].split()
						look_up=self.liststore_combobox[ii][1].split()
						src_value=orig_list[look_up.index(src_value.rstrip())]

					inp_update_token_value(self.param_list[pos_mirror_dest].filename, self.param_list[pos_mirror_dest].token, src_value)	

	def tree(self,tree_items,commands,base_dir,level,path,var_to_change,value_to_change):
			print level,tree_items
			i=tree_items[1][level]
			words=i.split()
			pass_var_to_change=var_to_change+" "+str(self.combo_box_list.index(tree_items[0][level]))
			print pass_var_to_change
			for ii in words:
				cur_dir=path+"/"+ii

				if not os.path.exists(cur_dir):
					os.makedirs(cur_dir)
					if level==0:
						f = open(cur_dir+'/scan.inp','w')
						f.write("data")
						f.close()

				pass_value_to_change=value_to_change+" "+ii

				if ((level+1)<len(tree_items[0])):
						self.tree(tree_items,commands,base_dir,level+1,cur_dir,pass_var_to_change,pass_value_to_change)
				else:
					new_values=pass_value_to_change.split()
					pos=pass_var_to_change.split()
					
					f_list=glob.iglob(os.path.join(base_dir, "*.inp"))
					for inpfile in f_list:
                         			shutil.copy(inpfile, cur_dir)

					shutil.copy(os.path.join(base_dir, "sim.opvdm"), cur_dir)

					os.chdir(cur_dir)
					
					for i in range(0, len(pos)):
						inp_update_token_value(self.param_list[int(pos[i])].filename, self.param_list[int(pos[i])].token, new_values[i])
					
					self.apply_mirror()
					self.apply_constant()	
					
					inp_update_token_value("physdir.inp", "#physdir", base_dir+"/phys/")
					inp_update_token_value("dump.inp", "#plot", "0")

					commands.append(os.getcwd())


	def make_sim_dir(self):
		if os.path.isdir(self.sim_dir)==False:
			os.makedirs(self.sim_dir)


	def callback_stop(self, widget, data=None):
		self.myserver.stop()
		cmd = 'killall '+self.exe_name
		ret= os.system(cmd)

	def callback_simulate(self, widget, data=None):

		base_dir=os.getcwd()
		run=True

		if len(self.liststore_combobox) == 0:
			message = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
			message.set_markup("You have not selected any parameters to scan through.  Use the add button.")
			message.run()
			message.destroy()
			return


		if self.sim_name=="":
			message = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
			message.set_markup("No sim dir name")
			message.run()
			message.destroy()
			return

		self.make_sim_dir()
		dirs_to_del=[]
		ls=os.listdir(self.sim_dir)
		print ls
		for i in range(0, len(ls)):
			full_name=self.sim_dir+ls[i]
			if os.path.isdir(full_name):
				if os.path.isfile(full_name+'/scan.inp'):
					dirs_to_del.append(full_name)

		if (len(dirs_to_del)!=0):

			settings = gtk.settings_get_default()
			settings.set_property('gtk-alternative-button-order', True)

			dialog = gtk.Dialog()
			cancel_button = dialog.add_button(gtk.STOCK_YES, gtk.RESPONSE_YES)

			ok_button = dialog.add_button(gtk.STOCK_NO, gtk.RESPONSE_NO)
			ok_button.grab_default()

			help_button = dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

			label = gtk.Label("Should I delete the old simualtions first?:\n"+"\n".join(dirs_to_del))
			dialog.vbox.pack_start(label, True, True, 0)
			label.show()

			dialog.set_alternative_button_order([gtk.RESPONSE_YES, gtk.RESPONSE_NO,
						       gtk.RESPONSE_CANCEL])

			#dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_QUESTION,  gtk.BUTTONS_YES_NO, str("Should I delete the old simualtions first?:\n"+"\n".join(dirs_to_del)))
			response = dialog.run()
			
			if response == gtk.RESPONSE_YES:
				for i in range(0, len(dirs_to_del)):
					print "Deleting:",dirs_to_del[i]
					shutil.rmtree(dirs_to_del[i])
			elif response == gtk.RESPONSE_NO:
				print "Not deleting"
			elif response == gtk.RESPONSE_CANCEL:
				run=False
				print "Cancel"

			dialog.destroy()


		for i in range(0,len(self.liststore_combobox)):
			found=False
			for ii in range(0,len(self.liststore_op_type)):
				if self.liststore_combobox[i][2]==self.liststore_op_type[ii][0]:
					found=True
			if found==False:
				run=False

				md = gtk.MessageDialog(None, 
				0, gtk.MESSAGE_ERROR, 
				gtk.BUTTONS_CLOSE, self.liststore_combobox[i][2]+"Not valid")
				md.run()
				md.destroy()
				break



		if run==True:
			commands=[]
			tree_items=[[],[],[]]
			for i in range(0,len(self.liststore_combobox)):
				if self.liststore_combobox[i][2]=="scan":
					tree_items[0].append(self.liststore_combobox[i][0])
					tree_items[1].append(self.liststore_combobox[i][1])
					tree_items[2].append(self.liststore_combobox[i][2])


			self.tree(tree_items,commands,base_dir,0,self.sim_dir,"","")
		
			self.myserver.init()
			for i in range(0, len(commands)):
				self.myserver.add_job(commands[i])


			self.myserver.start(self.sim_dir,self.exe_command)


			self.save_combo()

		os.chdir(base_dir)
		gc.collect()

	def callback_plot_results(self, widget, data=None):
		self.plot_results(self.last_plot_data)

	def callback_last_menu_click(self, widget, data):
		self.plot_results(data)

	def callback_reopen_xy_window(self, widget, data=None):

		if len(self.plotted_graphs)>0:
			pos=len(self.plotted_graphs)-1
			plot_data=plot_command_class()
			plot_data.file0=self.plotted_graphs[pos].file0
			plot_xy_window=plot_dlg_class(gtk.WINDOW_TOPLEVEL)
			plot_xy_window.my_init(plot_data)
			plot_now=plot_xy_window.my_run(plot_data)

			if plot_now==True:
				self.plotted_graphs.append(plot_data,True)
				self.plot_results(plot_data)

	def callback_gen_plot_command(self, widget, data=None):
		dialog = gtk.FileChooserDialog("File to plot",
               None,
               gtk.FILE_CHOOSER_ACTION_OPEN,
               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
		dialog.set_current_folder(self.sim_dir)
		filter = gtk.FileFilter()
		filter.set_name("Data files")
		filter.add_pattern("*.dat")
		dialog.add_filter(filter)

		filter = gtk.FileFilter()
		filter.set_name("Input files")
		filter.add_pattern("*.inp")
		dialog.add_filter(filter)

		dialog.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)


		response = dialog.run()
		if response == gtk.RESPONSE_OK:
			full_file_name=dialog.get_filename()
			dialog.destroy()
			#print cur_dir=os.getcwd()
			#print full_file_name
			file_name=os.path.basename(full_file_name)

			plot_data=plot_command_class()
			plot_data.path=self.sim_dir
			plot_data.example_file0=full_file_name
			plot_data.example_file1=full_file_name

			plot_now=False
			if check_info_file(file_name)==True:
				plot_data.file0=file_name
				plot_xy_window=plot_dlg_class(gtk.WINDOW_TOPLEVEL)
				plot_xy_window.my_init(plot_data)
				plot_now=plot_xy_window.my_run(plot_data)
			else:
				plot_data.file0=file_name
				plot_data.tag0=""
				plot_data.file1=""
				plot_data.tag1=""
				plot_now=True

			if plot_now==True:
				self.plotted_graphs.append(plot_data,True)

				self.plot_results(plot_data)

		else:
			print 'Closed, no files selected'
			dialog.destroy()

	def gen_plot_line(self,dirname,plot_tokens):
		if plot_tokens.file1=="":
			f = open(dirname+"/"+plot_tokens.file0,'r')
			values=f.readline()
			f.close()
			return values
		else:
			v0=inp_get_token_value(dirname+"/"+plot_tokens.file0, plot_tokens.tag0)
			v1=inp_get_token_value(dirname+"/"+plot_tokens.file1, plot_tokens.tag1)
			values=v0+" "+v1+"\n"
			return values

	def gen_infofile_plot(self,result_in,path,plot_tokens):
		file_name=os.path.splitext(plot_tokens.file0)[0]+plot_tokens.tag0+"#"+os.path.splitext(plot_tokens.file1)[0]+plot_tokens.tag1+".dat"
		values=""
		result=[]

		#only allow files from real simulations in the list
		for i in range(0,len(result_in)):
			test_name=os.path.dirname(result_in[i])+'/sim.opvdm'
			if os.path.isfile(test_name):
				result.append(result_in[i])

		#pull out first item
		ittr_path=os.path.dirname(result[0])
		ittr_path=ittr_path[len(self.sim_dir):]
		#check it's depth
		depth=ittr_path.count('/')


		if depth==0:
			mydirs=[""]
		else:
			mydirs=[]
			for i in result:
				ittr_path=os.path.dirname(i)
				ittr_path=ittr_path[len(self.sim_dir):]
				ittr_path=ittr_path.split('/')
				if mydirs.count(ittr_path[0])==0:
					mydirs.append(ittr_path[0])

		

		data=["" for x in range(len(mydirs))]

		for i in range(0, len(result)):
			cur_sim_path=os.path.dirname(result[i])+'/'
			if cur_sim_path!=path:
				print result[i],cur_sim_path
				values=self.gen_plot_line(cur_sim_path,plot_tokens)

				if depth==0:
					pos=0
				else:
					ittr_path=os.path.dirname(result[i])
					ittr_path=ittr_path[len(self.sim_dir):]
					ittr_path=ittr_path.split('/')
					pos=mydirs.index(ittr_path[0])

				print pos
				data[pos]=data[pos]+values
				print data[pos]
		plot_files=[]
		plot_labels=[]
		for i in range(0,len(mydirs)):
			newplotfile=path+'/'+mydirs[i]+'/'+file_name
			plot_files.append(newplotfile)
			plot_labels.append(os.path.basename(mydirs[i]))
			f = open(newplotfile,'w')
			f.write(data[i])
			f.close()

		plot_gen(plot_files,plot_labels,plot_tokens)


	def plot_results(self,plot_tokens):
		path=plot_tokens.path
		file_name=plot_tokens.file0
		result=[]

		#search for the files
		return_file_list(result,path,file_name)

		num_list=[]

		#remove the file name in the base_dir
		test_file=path+file_name
		if test_file in result:
		    result.remove(test_file)

		#attemlt to sort list in numeric order
		try:
			for i in range(0, len(result)):
				dir_name=os.path.basename(os.path.dirname(result[i]))
				if dir_name=="dynamic":
					dir_name=os.path.basename(os.path.dirname(os.path.dirname(result[i])))
				num_list.append(float(dir_name))

			num_list, result = zip(*sorted(zip(num_list, result)))
		except:
			print "There are stings in the list I can not order it"

		#if it is an info file then deal with it
		print check_info_file(file_name),file_name,plot_tokens.file0,plot_tokens.file1,plot_tokens.tag0,plot_tokens.tag1
		if (check_info_file(file_name)==True):
			self.gen_infofile_plot(result,path,plot_tokens)
		else:
			mygraph=plot_data()
			ret=mygraph.find_file(result[0],None)
			if ret==False:
				message = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
				message.set_markup("This file "+file_name+" is not in the data base please file a bug report..")
				message.run()
				message.destroy()
				return
			plot_labels=[]
			#build plot labels
			for i in range(0,len(result)):
				text=result[i][len(self.sim_dir):len(result[i])-1-len(os.path.basename(result[i]))]
				if text.endswith("/dynamic"):
					text=text[:-8]
				plot_labels.append(text)

			plot_gen(result,plot_labels,None)
			print result
		self.plot_open.set_sensitive(True)

		self.last_plot_data=plot_tokens

	def save_combo(self):
		self.make_sim_dir()
		a = open(self.sim_dir+"/opvdm_gui_config.inp", "w")
		a.write(str(len(self.liststore_combobox))+"\n")


		for item in self.liststore_combobox:
			a.write(item[0]+"\n")
			a.write(item[1]+"\n")
			a.write(item[2]+"\n")	
		
		a.close()


	def combo_changed(self, widget, path, text, model):
		model[path][0] = text
		self.rebuild_liststore_op_type()
		self.save_combo()

	def combo_mirror_changed(self, widget, path, text, model):
		model[path][2] = text
		if model[path][2]!="constant":
			if model[path][2]!="scan":
				model[path][1] = "mirror"
		self.save_combo()


	def text_changed(self, widget, path, text, model):
		model[path][1] = text
		self.save_combo()


	def reload_liststore(self):
		self.liststore_combobox.clear()

		file_name=self.sim_dir+'opvdm_gui_config.inp'

		if os.path.isfile(file_name)==True:
			f=open(file_name)
			config = f.readlines()
			f.close()

			for ii in range(0, len(config)):
				config[ii]=config[ii].rstrip()

			pos=0
			mylen=int(config[0])
			pos=pos+1
			for i in range(0, mylen):
				self.liststore_combobox.append([config[pos], config[pos+1], config[pos+2]])
				pos=pos+3


	def on_treeview_button_press_event(self, treeview, event):
		if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
			self.popup_menu.popup(None, None, None, event.button, event.time)
			pass

	def callback_close(self,widget):
		self.hide()

	def rebuild_liststore_op_type(self):
		self.liststore_op_type.clear()
		self.liststore_op_type.append(["scan"])
		self.liststore_op_type.append(["constant"])

		for i in range(0,len(self.liststore_combobox)):
			if self.liststore_combobox[i][0]!="Select parameter":
				self.liststore_op_type.append([self.liststore_combobox[i][0]])
	def set_tab_caption(self,name):
		mytext=name
		if len(mytext)<10:
			for i in range(len(mytext),10):
				mytext=mytext+" "
		self.tab_label.set_text(mytext)

	def set_visible(self,value):
		if value==True:
			self.visible=True
			self.config.set_value("#visible",True)
			self.show()
		else:
			self.visible=False
			self.config.set_value("#visible",False)
			self.hide()

	def init(self,myserver,tooltips,status_bar,context_id,param_list,exe_command,tab_label,sim_name):

		self.config=config()
		self.sim_name=sim_name
		self.clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
		self.popup_menu = gtk.Menu()
		menu_item = gtk.MenuItem("Copy")
		menu_item.connect("activate", self.callback_copy_item)
		self.popup_menu.append(menu_item)

		menu_item = gtk.MenuItem("Paste")
		menu_item.connect("activate", self.callback_paste_item)
		self.popup_menu.append(menu_item)

		menu_item = gtk.MenuItem("Delete")
		menu_item.connect("activate", self.callback_delete_item)
		self.popup_menu.append(menu_item)
		self.popup_menu.show_all()

		self.myserver=myserver
		self.tooltips=tooltips
		self.status_bar=status_bar
		self.context_id=context_id
		self.param_list=param_list
		self.exe_command=exe_command
		self.tab_label=tab_label
		self.liststore_op_type = gtk.ListStore(str)


		self.sim_dir=os.getcwd()+'/'+sim_name+'/'
		self.tab_name=os.path.basename(os.path.normpath(self.sim_dir))

		self.status_bar.push(self.context_id, self.sim_dir)
		self.set_tab_caption(self.tab_name)
		toolbar = gtk.Toolbar()
		toolbar.set_style(gtk.TOOLBAR_ICONS)
		toolbar.set_size_request(-1, 50)
		pos=0

		#image = gtk.Image()
		#image.set_from_file(find_data_file("gui/arrow-right.png"))
		open_plot = gtk.ToolButton(gtk.STOCK_MEDIA_PLAY)
		open_plot.connect("clicked", self.callback_simulate)
		self.tooltips.set_tip(open_plot, "Parameter scan")
		toolbar.insert(open_plot, pos)
		pos=pos+1

	        #image = gtk.Image()
   		#image.set_from_file(find_data_file("gui/media-playback-pause-7.png"))
		self.stop = gtk.ToolButton(gtk.STOCK_MEDIA_PAUSE)
		self.tooltips.set_tip(self.stop, "Stop the simulation")
		self.stop.connect("clicked", self.callback_stop)
		toolbar.insert(self.stop, pos)
		pos=pos+1

		sep = gtk.SeparatorToolItem()
		sep.set_draw(True)
		sep.set_expand(False)
		toolbar.insert(sep, pos)
		pos=pos+1

		image = gtk.Image()
		image.set_from_file(find_data_file("gui/plot.png"))
		plot_select = gtk.MenuToolButton(image,"hello")
		plot_select.connect("clicked", self.callback_gen_plot_command)
		self.tooltips.set_tip(plot_select, "Find a file to plot")

		self.plotted_graphs = used_files_menu()
		self.plotted_graphs.init(self.sim_dir+'gui_last_menu.inp',self.callback_last_menu_click)
		self.plotted_graphs.reload_list()
		plot_select.set_menu(self.plotted_graphs.menu)
		toolbar.insert(plot_select, pos)

		pos=pos+1

	        image = gtk.Image()
   		image.set_from_file(self.icon_theme.lookup_icon("view-refresh", 32, 0).get_filename())
		self.plot_open = gtk.ToolButton(image)
		self.plot_open.connect("clicked", self.callback_plot_results)
		self.plot_open.set_sensitive(False)
		self.tooltips.set_tip(self.plot_open, "Replot the graph")
		toolbar.insert(self.plot_open, pos)
		pos=pos+1

		sep = gtk.SeparatorToolItem()
		sep.set_draw(True)
		sep.set_expand(False)
		toolbar.insert(sep, pos)
		pos=pos+1

		add = gtk.ToolButton(gtk.STOCK_ADD)
		add.connect("clicked", self.callback_add_item)
		self.tooltips.set_tip(add, "Add parameter to scan")
		toolbar.insert(add, pos)
		pos=pos+1


		remove = gtk.ToolButton(gtk.STOCK_CLEAR)
		remove.connect("clicked", self.callback_delete_item)
		self.tooltips.set_tip(remove, "Delete item")
		toolbar.insert(remove, pos)
		pos=pos+1

		move = gtk.ToolButton(gtk.STOCK_GO_DOWN)
		move.connect("clicked", self.callback_move_down)
		self.tooltips.set_tip(move, "Move down")
		toolbar.insert(move, pos)
		pos=pos+1

		sep = gtk.SeparatorToolItem()
		sep.set_draw(True)
		sep.set_expand(False)
		toolbar.insert(sep, pos)
		pos=pos+1

		quick = gtk.ToolButton(gtk.STOCK_INDEX)
		quick.connect("clicked", self.callback_show_list)
		self.tooltips.set_tip(quick, "Show quick selector")
		toolbar.insert(quick, pos)
		pos=pos+1

		#reopen_xy = gtk.ToolButton(gtk.STOCK_SELECT_COLOR)
		#reopen_xy.connect("clicked", self.callback_reopen_xy_window)
		#self.tooltips.set_tip(reopen_xy, "Reopen xy window selector")
		#toolbar.insert(reopen_xy, pos)
		#pos=pos+1

		toolbar.show_all()
		self.pack_start(toolbar, False, False, 0)#.add()


		self.combo_box_list = []
		for item in range(0, len(self.param_list)):
			self.combo_box_list.append(self.param_list[item].name)

		liststore_manufacturers = gtk.ListStore(str)
		for item in self.combo_box_list:
		    liststore_manufacturers.append([item])

		self.liststore_combobox = gtk.ListStore(str, str, str)

		self.config.load(self.sim_dir)
		self.visible=self.config.get_value("#visible",True)
		self.reload_liststore()


		self.treeview = gtk.TreeView(self.liststore_combobox)
		self.treeview.connect("button-press-event", self.on_treeview_button_press_event)
		self.treeview.set_size_request(-1, 400)

		self.select_param_window=select_param()
		self.select_param_window.init(self.liststore_combobox,self.treeview,param_list)

		column_text = gtk.TreeViewColumn("Values")
		column_combo = gtk.TreeViewColumn("Parameter to change")
		column_mirror = gtk.TreeViewColumn("Mirror")
		self.treeview.append_column(column_combo)
		self.treeview.append_column(column_text)
		self.treeview.append_column(column_mirror)

		cellrenderer_combo = gtk.CellRendererCombo()
		cellrenderer_combo.set_property("editable", True)
		cellrenderer_combo.set_property("model", liststore_manufacturers)
		cellrenderer_combo.set_property("text-column", 0)
		cellrenderer_combo.connect("edited", self.combo_changed, self.liststore_combobox)

		column_combo.pack_start(cellrenderer_combo, False)
		column_combo.set_min_width(240)
		column_combo.add_attribute(cellrenderer_combo, "text", 0)

		cellrenderer_mirror = gtk.CellRendererCombo()
		cellrenderer_mirror.set_property("editable", True)
		self.rebuild_liststore_op_type()
		cellrenderer_mirror.set_property("model", self.liststore_op_type)
		cellrenderer_mirror.set_property("text-column", 0)
		cellrenderer_mirror.connect("edited", self.combo_mirror_changed, self.liststore_combobox)

		column_mirror.pack_start(cellrenderer_mirror, False)
		column_mirror.set_min_width(240)
		column_mirror.add_attribute(cellrenderer_mirror, "text", 2)

		cellrenderer_text = gtk.CellRendererText()
		cellrenderer_text.set_property("editable", True)
		cellrenderer_text.connect("edited", self.text_changed, self.liststore_combobox)
		cellrenderer_text.props.wrap_width = 400
		cellrenderer_text.props.wrap_mode = gtk.WRAP_WORD
		column_text.pack_start(cellrenderer_text, False)
		column_text.set_min_width(240)
		column_text.add_attribute(cellrenderer_text, "text", 1)



		#window.connect("destroy", lambda w: gtk.main_quit())

		self.pack_start(self.treeview, False, True, 0)
		self.treeview.show()
		self.show_all()
		if self.visible==False:
			self.hide()

