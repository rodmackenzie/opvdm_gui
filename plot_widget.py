import pygtk
pygtk.require('2.0')
import gtk
import re
import sys
import os
import shutil
from token_lib import tokens
from numpy import *
from util import pango_to_gnuplot
from plot import plot_data
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from plot_export import plot_export 
from numpy import arange, sin, pi, zeros
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg
from matplotlib.figure import Figure
from plot_info import plot_info
from util import zip_get_data_file
from util import read_xyz_data
import matplotlib.ticker as ticker
from gui_util import dlg_get_text
from inp import inp_load_file
from inp import inp_write_lines_to_file
from inp import inp_search_token_value
from inp import inp_save_lines
from util import str2bool
from util import numbers_to_latex
from util import pygtk_to_latex_subscript
from util import fx_with_units
from plot_state import plot_state

class NavigationToolbar(NavigationToolbar2GTKAgg):
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar2GTKAgg.toolitems if
                 t[0] in ('Home', 'Pan', 'Zoom', 'Subplots')]


class plot_widget(gtk.VBox):

	def on_key_press_event(self,widget, event):
		keyname = gtk.gdk.keyval_name(event.keyval)
		#print "Key %s (%d) was pressed" % (keyname, event.keyval)
		if keyname=="a":
			self.do_plot()

		if keyname=="g":
			if self.my_plot_state.grid==False:
				for i in range(0,len(self.ax)):
					self.ax[i].grid(True)
				self.my_plot_state.grid=True
			else:
				for i in range(0,len(self.ax)):
					self.ax[i].grid(False)
				self.my_plot_state.grid=False
		if keyname=="r":
			if self.lx==None:
				for i in range(0,len(self.ax)):
					self.lx = self.ax[i].axhline(color='k')
					self.ly = self.ax[i].axvline(color='k')
			self.lx.set_ydata(self.ydata)
			self.ly.set_xdata(self.xdata)

		if keyname=="l":
			if self.my_plot_state.logy==True:
				self.my_plot_state.logy=False
				for i in range(0,len(self.ax)):
					self.ax[i].set_yscale("linear")
			else:
				self.my_plot_state.logy=True
				for i in range(0,len(self.ax)):
					self.ax[i].set_yscale("log")

		if keyname=="L":
			if self.my_plot_state.logx==True:
				self.my_plot_state.logx=False
				for i in range(0,len(self.ax)):
					self.ax[i].set_xscale("linear")
			else:
				self.my_plot_state.logx=True
				for i in range(0,len(self.ax)):
					self.ax[i].set_xscale("log")

		if keyname=="q":
			self.win.destroy()

		if keyname == "c":
			if event.state == gtk.gdk.CONTROL_MASK:
				self.do_clip()

		self.fig.canvas.draw()
		self.save_state()

	def do_clip(self):
		snap = self.canvas.get_snapshot()
		pixbuf = gtk.gdk.pixbuf_get_from_drawable(None, snap, snap.get_colormap(),0,0,0,0,snap.get_size()[0], snap.get_size()[1])
		clip = gtk.Clipboard()
		clip.set_image(pixbuf)



	def mouse_move(self,event):
		#print event.xdata, event.ydata
		self.xdata=event.xdata
		self.ydata=event.ydata
	
		#self.fig.canvas.draw()

		#except:
		#	print "Error opening file ",file_name

	def read_data_2d(self,x,y,z,file_name):
		found,lines=zip_get_data_file(file_name)
		if found==True:

			for i in range(0, len(lines)):
				lines[i]=re.sub(' +',' ',lines[i])
				lines[i]=re.sub('\t',' ',lines[i])
				lines[i]=lines[i].rstrip()
				sline=lines[i].split(" ")
				if len(sline)==2:
					if (lines[i][0]!="#"):
						x.append(float(lines[i].split(" ")[0]))
						y.append(float(lines[i].split(" ")[1]))
						z.append(float(lines[i].split(" ")[2]))
			return True
		else:
			return False


	def sub_zero_frame(self,t,s,i):
		tt=[]
		ss=[]
		z=[]
		#print self.zero_frame_enable
		if self.zero_frame_enable==True:
			if read_xyz_data(tt,ss,z,self.zero_frame_list[i])==True:
				for ii in range(0,len(t)):
					s[ii]=s[ii]-ss[ii]

	def read_data_file(self,t,s,z,index):
		if read_xyz_data(t,s,z,self.input_files[index])==True:
			self.sub_zero_frame(t,s,index)
			my_min=0.0;
				

			for ii in range(0,len(t)):
				t[ii]=t[ii]*self.my_plot_state.x_mul
				s[ii]=s[ii]*self.my_plot_state.y_mul

				if self.my_plot_state.invert_y==True:
					s[ii]=-s[ii]					

				if self.my_plot_state.subtract_first_point==True:
					if ii==0:
						val=s[0]
					s[ii]=s[ii]-val

	
			if self.my_plot_state.add_min==True:
				my_min=min(s)
				for ii in range(0,len(t)):
					s[ii]=s[ii]-my_min

			if self.my_plot_state.normalize==True:
				local_max=max(s)
				for ii in range(0,len(t)):
					if s[ii]!=0:
						s[ii]=s[ii]/local_max
					else:
						s[ii]=0.0


			plot_number=self.plot_id[index]
			#print plot_number, number_of_plots,self.plot_id
			if self.my_plot_state.ymax!=-1:
				self.ax[plot_number].set_ylim((self.my_plot_state.ymin,self.my_plot_state.ymax))
			return True
		else:
			return False

	def do_plot(self):
		print "in do plot"
		plot_number=0

		self.fig.clf()
		self.fig.subplots_adjust(bottom=0.2)
		self.fig.subplots_adjust(bottom=0.2)
		self.fig.subplots_adjust(left=0.1)
		self.fig.subplots_adjust(hspace = .001)
		if self.plot_title=="":
			self.fig.suptitle(self.mygraph.read.title)
		else:
			self.fig.suptitle(self.plot_title)

		self.ax=[]
		number_of_plots=max(self.plot_id)+1
		if number_of_plots>1:
			yloc = plt.MaxNLocator(4)
		else:
			yloc = plt.MaxNLocator(10)




		for i in range(0,number_of_plots):
			self.ax.append(self.fig.add_subplot(number_of_plots,1,i+1, axisbg='white'))
			#Only place label on bottom plot
			if i==number_of_plots-1:
				self.ax[i].set_xlabel(self.my_plot_state.x_label+" ("+self.my_plot_state.x_units+")")

			else:
				self.ax[i].tick_params(axis='x', which='both', bottom='off', top='off',labelbottom='off') # labels along the bottom edge are off

			#Only place y label on center plot
			if self.my_plot_state.normalize==True or self.my_plot_state.norm_to_peak_of_all_data==True:
				y_text="Normalized "+self.my_plot_state.y_label
				y_units="au"
			else:
				y_text=self.my_plot_state.y_label
				y_units=self.my_plot_state.y_units
			if i==math.trunc(number_of_plots/2):
				self.ax[i].set_ylabel(y_text+" ("+y_units+")")

			if self.my_plot_state.logx==True:
				self.ax[i].set_xscale("log")

			if self.my_plot_state.logy==True:
				self.ax[i].set_yscale("log")


		lines=[]
		files=[]

		my_max=1.0

		if self.mygraph.read.type=="xy":

			all_max=1.0
			if self.my_plot_state.norm_to_peak_of_all_data==True:
				m=[]
				my_max=-1e40
				for i in range(0, len(self.input_files)):
					t=[]
					s=[]
					z=[]
					if self.read_data_file(t,s,z,i)==True:
						if max(s)>my_max:
							my_max=max(s)
				all_max=my_max

			for i in range(0, len(self.input_files)):
				#t,s = loadtxt(self.input_files[i], unpack=True)
				t=[]
				s=[]
				z=[]
				if self.read_data_file(t,s,z,i)==True:
					#print "z==",z
					if all_max!=1.0:
						for ii in range(0,len(s)):
							s[ii]=s[ii]/all_max
					#print len(self.ax),plot_number,i,len(self.color),len(self.marker)
					Ec, = self.ax[plot_number].plot(t,s, linewidth=3 ,alpha=1.0,color=self.color[i],marker=self.marker[i])

					#label data if required
					if self.my_plot_state.label_data==True:
						for ii in range(0,len(t)):
							if z[ii]!="":
								self.ax[plot_number].annotate(fx_with_units(float(z[ii])),xy = (t[ii], s[ii]), xytext = (-20, 20),textcoords = 'offset points', ha = 'right', va = 'bottom',bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))

					if number_of_plots>1:
						self.ax[plot_number].yaxis.set_major_formatter(ticker.FormatStrFormatter('%0.1e'))
						if min(s)!=max(s):
							self.ax[plot_number].yaxis.set_ticks(arange(min(s), max(s), (max(s)-min(s))/4.0 ))

					if self.labels[i]!="":
						files.append("$"+numbers_to_latex(str(self.labels[i]))+" "+self.my_plot_state.key_units+"$")
						lines.append(Ec)

			self.lx = None
			self.ly = None
			if self.my_plot_state.legend_pos=="No key":
				self.ax[plot_number].legend_ = None
			else:
				legend=self.fig.legend(lines, files, self.my_plot_state.legend_pos)
			
		else:
			x=[]
			y=[]
			z=[]

			if self.read_data_2d(x,y,z,self.input_files[0])==True:
				maxx=-1
				maxy=-1
				for i in range(0,len(z)):
					if x[i]>maxx:
						maxx=x[i]

					if y[i]>maxy:
						maxy=y[i]

				maxx=maxx+1
				maxy=maxy+1

				data = zeros((maxy,maxx))


				for i in range(0,len(z)):
					data[y[i]][x[i]]= random.random()+5
					self.ax[0].text(x[i], y[i]+float(maxy)/float(len(z))+0.1,'%.1e' %  z[i], fontsize=12)

				#fig, ax = plt.subplots()
				self.ax[0].pcolor(data,cmap=plt.cm.Blues)

				self.ax[0].invert_yaxis()
				self.ax[0].xaxis.tick_top()

		#self.fig.tight_layout(pad=0.0, w_pad=0.0, h_pad=0.0)
		self.fig.canvas.draw()
		print "exit do plot"

	def callback_plot_save(self, widget, data=None):
		dialog = gtk.FileChooserDialog("Directory to make a gnuplot script..",
                               None,
                               gtk.FILE_CHOOSER_ACTION_OPEN,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_SAVE, gtk.RESPONSE_OK))
		print os.path.basename(self.output_file),os.path.dirname(self.output_file)
		dialog.set_current_folder(os.path.dirname(self.output_file))
		dialog.set_default_response(gtk.RESPONSE_OK)
		dialog.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)

		filter = gtk.FileFilter()
		filter.set_name("png file")
		filter.add_pattern("*.png")
		dialog.add_filter(filter)

		filter = gtk.FileFilter()
		filter.set_name("gnuplot script")
		filter.add_pattern("*.")
		dialog.add_filter(filter)

		dialog.set_current_name(os.path.basename(self.output_file))

		response = dialog.run()
		if response == gtk.RESPONSE_OK:
			print "Logscale x = ",self.mygraph.read.logscale_x
			plot_export(dialog.get_filename(),self.input_files,self.my_plot_state,self.fig)

		elif response == gtk.RESPONSE_CANCEL:
		    print 'Closed, no dir selected'

		dialog.destroy()

	def load_data(self,input_files,plot_id,labels,plot_token,config_file,units):
		self.config_file=config_file
		self.output_file=os.path.splitext(config_file)[0]+".png"
		self.labels=labels
		self.plot_id=plot_id
		if len(input_files)!=len(labels):
			return
		self.input_files=input_files
		self.plot_token=plot_token
		self.mygraph=plot_data()
		ret=self.mygraph.find_file(self.input_files[0],self.plot_token)
		if ret==True:
			#print "Rod",input_files
			title=self.mygraph.read.title
			self.win.set_title(title+" - www.opvdm.com")

			if (self.mygraph.read.logscale_x==1):
				self.my_plot_state.logx=True
	
			if (self.mygraph.read.logscale_y==1):
				self.my_plot_state.logy=True

			self.my_plot_state.x_label=self.mygraph.read.x_label
			self.my_plot_state.y_label=self.mygraph.read.y_label
			self.my_plot_state.x_units=self.mygraph.read.x_units
			self.my_plot_state.y_units=self.mygraph.read.y_units
			self.my_plot_state.x_mul=self.mygraph.read.x_mul
			self.my_plot_state.y_mul=self.mygraph.read.y_mul
			lines=[]
			if self.load_state()==False:
				self.save_state()
				print "Failed to load",self.config_file

			else:
				print "Loaded OK",self.config_file

			if self.my_plot_state.key_units=="":
				self.my_plot_state.key_units=pygtk_to_latex_subscript(units)

			test_file=self.input_files[0]
			for i in range(0,len(self.input_files)):
				if os.path.isfile(self.input_files[i]):
					test_file=self.input_files[i]

			print "test_file=",test_file
			print "self.plot_token=",self.plot_token

			self.mygraph.find_file(test_file,self.plot_token)
			print "Exit here"

	def load_state(self):
		lines=[]
		if self.config_file!="":
			if inp_load_file(lines,self.config_file)==True:
				self.my_plot_state.logy=str2bool(inp_search_token_value(lines, "#logy"))
				self.my_plot_state.logx=str2bool(inp_search_token_value(lines, "#logx"))
				self.my_plot_state.grid=str2bool(inp_search_token_value(lines, "#grid"))
				self.my_plot_state.invert_y=str2bool(inp_search_token_value(lines, "#invert_y"))
				self.my_plot_state.normalize=str2bool(inp_search_token_value(lines, "#normalize"))
				self.my_plot_state.norm_to_peak_of_all_data=str2bool(inp_search_token_value(lines, "#norm_to_peak_of_all_data"))
				self.my_plot_state.subtract_first_point=str2bool(inp_search_token_value(lines, "#subtract_first_point"))
				self.my_plot_state.add_min=str2bool(inp_search_token_value(lines, "#add_min"))
				self.plot_token.file0=inp_search_token_value(lines, "#file0")
				self.plot_token.file1=inp_search_token_value(lines, "#file1")
				self.plot_token.file2=inp_search_token_value(lines, "#file2")
				self.plot_token.tag0=inp_search_token_value(lines, "#tag0")
				self.plot_token.tag1=inp_search_token_value(lines, "#tag1")
				self.plot_token.tag2=inp_search_token_value(lines, "#tag2")
				self.my_plot_state.legend_pos=inp_search_token_value(lines, "#legend_pos")
				self.my_plot_state.key_units=inp_search_token_value(lines, "#key_units")
				self.my_plot_state.label_data=str2bool(inp_search_token_value(lines, "#label_data"))


				myitem=self.item_factory.get_item("/Math/Subtract first point")
				myitem.set_active(self.my_plot_state.subtract_first_point)

				myitem=self.item_factory.get_item("/Math/Add min point")
				myitem.set_active(self.my_plot_state.add_min)

				myitem=self.item_factory.get_item("/Math/Invert y-axis")
				myitem.set_active(self.my_plot_state.invert_y)

				myitem=self.item_factory.get_item("/Math/Norm to 1.0 y")
				myitem.set_active(self.my_plot_state.normalize)

				myitem=self.item_factory.get_item("/Math/Norm to peak of all data")
				myitem.set_active(self.my_plot_state.norm_to_peak_of_all_data)
				return True
		return False

	def save_state(self):
		if self.config_file!="":
			lines=[]
			lines.append("#logy")
			lines.append(str(self.my_plot_state.logy))
			lines.append("#logx")
			lines.append(str(self.my_plot_state.logx))
			lines.append("#grid")
			lines.append(str(self.my_plot_state.grid))
			lines.append("#invert_y")
			lines.append(str(self.my_plot_state.invert_y))
			lines.append("#normalize")
			lines.append(str(self.my_plot_state.normalize))
			lines.append("#norm_to_peak_of_all_data")
			lines.append(str(self.my_plot_state.norm_to_peak_of_all_data))
			lines.append("#subtract_first_point")
			lines.append(str(self.my_plot_state.subtract_first_point))
			lines.append("#add_min")
			lines.append(str(self.my_plot_state.add_min))
			lines.append("#file0")
			lines.append(self.plot_token.file0)
			lines.append("#file1")
			lines.append(self.plot_token.file1)
			lines.append("#file2")
			lines.append(self.plot_token.file2)
			lines.append("#tag0")
			lines.append(self.plot_token.tag0)
			lines.append("#tag1")
			lines.append(self.plot_token.tag1)
			lines.append("#tag2")
			lines.append(self.plot_token.tag2)
			lines.append("#legend_pos")
			lines.append(self.my_plot_state.legend_pos)
			lines.append("#key_units")
			lines.append(self.my_plot_state.key_units)
			lines.append("#label_data")
			lines.append(str(self.my_plot_state.label_data))
			lines.append("#ver")
			lines.append("1.0")
			lines.append("#end")

			inp_save_lines(self.config_file,lines)

	def gen_colors_black(self,repeat_lines):
		#make 100 black colors
		marker_base=["","x","o"]
		c_tot=[]
		base=[[0.0,0.0,0.0]]
		self.marker=[]
		self.color=[]
		for i in range(0,100):
			for n in range(0,repeat_lines):
				self.color.append([base[0][0],base[0][1],base[0][2]])
				self.marker.append(marker_base[n])

	def gen_colors(self,repeat_lines):
		base=[[0.0,0.0,1.0],[0.0,1.0,0.0],[1.0,0.0,0.0],[0.0,1.0,1.0],[1.0,1.0,0.0],[1.0,0.0,1.0]]
		c_tot=[]
		self.marker=[]
		marker_base=["","x","o"]
		mul=1.0
		self.color=[]
		for i in range(0,len(base)):
			for n in range(0,repeat_lines):
				c_tot.append([base[i][0]*mul,base[i][1]*mul,base[i][2]*mul])
				self.marker.append(marker_base[n])
		mul=0.5
		for i in range(0,len(base)):
			for n in range(0,repeat_lines):
				c_tot.append([base[i][0]*mul,base[i][1]*mul,base[i][2]*mul])
				self.marker.append(marker_base[n])

		mul=0.7
		for i in range(0,len(base)):
			for n in range(0,repeat_lines):
				c_tot.append([base[i][0]*mul,base[i][1]*mul,base[i][2]*mul])
				self.marker.append(marker_base[n])

		mul=0.25
		for i in range(0,len(base)):
			for n in range(0,repeat_lines):
				c_tot.append([base[i][0]*mul,base[i][1]*mul,base[i][2]*mul])
				self.marker.append(marker_base[n])

		mul=0.165
		for i in range(0,len(base)):
			for n in range(0,repeat_lines):
				c_tot.append([base[i][0]*mul,base[i][1]*mul,base[i][2]*mul])
				self.marker.append(marker_base[n])

		mul=0.082500
		for i in range(0,len(base)):
			for n in range(0,repeat_lines):
				c_tot.append([base[i][0]*mul,base[i][1]*mul,base[i][2]*mul])
				self.marker.append(marker_base[n])

		self.color=c_tot

	def callback_black(self, data, widget):
		self.gen_colors_black(1)
		self.save_state()
		self.do_plot()

	def callback_rainbow(self, data, widget):
		self.gen_colors(1)
		self.save_state()
		self.do_plot()

	def callback_save(self, data, widget):
		plot_export(self.output_file,self.input_files,self.my_plot_state,self.fig)

	def callback_key(self, data, widget):
		self.my_plot_state.legend_pos=widget.get_label()
		self.save_state()
		self.do_plot()

	def callback_units(self, data, widget):
		units=dlg_get_text( "Units:", self.my_plot_state.key_units)
		if units!=None:
			self.my_plot_state.key_units=units
		self.save_state()
		self.do_plot()


	def callback_autoscale_y(self, data, widget):
		if widget.get_active()==True:
			self.my_plot_state.ymax=-1
			self.my_plot_state.ymin=-1
		else:
			xmin, xmax, ymin, ymax = self.ax[0].axis()
			self.my_plot_state.ymax=ymax
			self.my_plot_state.ymin=ymin

	def callback_normtoone_y(self, data, widget):
		if widget.get_active()==True:
			self.my_plot_state.normalize=True
		else:
			self.my_plot_state.normalize=False
		self.save_state()
		self.do_plot()

	def callback_norm_to_peak_of_all_data(self, data, widget):
		if widget.get_active()==True:
			self.my_plot_state.norm_to_peak_of_all_data=True
		else:
			self.my_plot_state.norm_to_peak_of_all_data=False
		self.save_state()
		self.do_plot()

	def callback_toggle_log_scale_y(self, widget, data):
		self.my_plot_state.logy=data.get_active()
		self.save_state()
		self.do_plot()

	def callback_toggle_log_scale_x(self, widget, data):
		self.my_plot_state.logx=data.get_active()
		self.save_state()
		self.do_plot()

	def callback_toggle_label_data(self, widget, data):
		self.my_plot_state.label_data=data.get_active()
		self.save_state()
		self.do_plot()

	def callback_toggle_invert_y(self, widget, data):
		self.my_plot_state.invert_y=data.get_active()
		self.save_state()
		self.do_plot()

	def callback_toggle_subtract_first_point(self, widget, data):
		self.my_plot_state.subtract_first_point=data.get_active()
		self.save_state()
		self.do_plot()

	def callback_toggle_add_min(self, widget, data):
		self.my_plot_state.add_min=data.get_active()
		self.save_state()
		self.do_plot()

	def callback_refresh(self, widget, data=None):
		self.save_state()
		self.do_plot()

	def init(self,in_window):
		self.zero_frame_enable=False
		self.zero_frame_list=[]
		#print type(in_window)
		self.plot_title=""
		self.gen_colors(1)
		#self.color =['r','g','b','y','o','r','g','b','y','o']
		self.win=in_window
		self.my_plot_state=plot_state()
		self.toolbar = gtk.Toolbar()
		self.toolbar.set_style(gtk.TOOLBAR_ICONS)
		self.toolbar.set_size_request(-1, 50)
		self.toolbar.show()
		self.config_file=""
		

		self.fig = Figure(figsize=(2.5,2), dpi=100)

		self.canvas = FigureCanvas(self.fig)  # a gtk.DrawingArea

		self.fig.canvas.mpl_connect('motion_notify_event', self.mouse_move)

		self.item_factory = gtk.ItemFactory(gtk.MenuBar, "<main>", None)

		menu_items = (
		    ( "/_File",         None,         None, 0, "<Branch>" ),
		    ( "/_File/Save",  None,         self.callback_save , 0, None ),
		    ( "/_File/Save As...",  None,         self.callback_plot_save , 0, None ),
		    ( "/_Key",         None,         None, 0, "<Branch>" ),
		    ( "/_Key/No key",  None,         self.callback_key , 0, "<RadioItem>", "gtk-save" ),
		    ( "/_Key/upper right",  None,         self.callback_key , 0, "<RadioItem>", "gtk-save" ),
		    ( "/_Key/upper left",  None,         self.callback_key , 0, "<RadioItem>", "gtk-save" ),
		    ( "/_Key/lower left",  None,         self.callback_key , 0, "<RadioItem>", "gtk-save" ),
		    ( "/_Key/lower right",  None,         self.callback_key , 0, "<RadioItem>", "gtk-save" ),
		    ( "/_Key/right",  None,         self.callback_key , 0, "<RadioItem>", "gtk-save" ),
		    ( "/_Key/center right",  None,         self.callback_key , 0, "<RadioItem>", "gtk-save" ),
		    ( "/_Key/lower center",  None,         self.callback_key , 0, "<RadioItem>", "gtk-save" ),
		    ( "/_Key/upper center",  None,         self.callback_key , 0, "<RadioItem>", "gtk-save" ),
		    ( "/_Key/center",  None,         self.callback_key , 0, "<RadioItem>", "gtk-save" ),
		    ( "/_Key/Units",  None,         self.callback_units , 0, None ),
		    ( "/_Color/Black",  None,         self.callback_black , 0, None ),
		    ( "/_Color/Rainbow",  None,         self.callback_rainbow , 0, None ),
		    ( "/_Axis/_Autoscale y",     None, self.callback_autoscale_y, 0, "<ToggleItem>", "gtk-save" ),
		    ( "/_Axis/_Set log scale y",     None, self.callback_toggle_log_scale_y, 0, "<ToggleItem>", "gtk-save" ),
		    ( "/_Axis/_Set log scale x",     None, self.callback_toggle_log_scale_x, 0, "<ToggleItem>", "gtk-save" ),
		    ( "/_Axis/_Label data",     None, self.callback_toggle_label_data, 0, "<ToggleItem>", "gtk-save" ),
		    ( "/_Math/_Subtract first point",     None, self.callback_toggle_subtract_first_point, 0, "<ToggleItem>", "gtk-save" ),
		    ( "/_Math/_Add min point",     None, self.callback_toggle_add_min, 0, "<ToggleItem>", "gtk-save" ),
		    ( "/_Math/_Invert y-axis",     None, self.callback_toggle_invert_y, 0, "<ToggleItem>", "gtk-save" ),
		    ( "/_Math/_Norm to 1.0 y",     None, self.callback_normtoone_y, 0, "<ToggleItem>", "gtk-save" ),
		    ( "/_Math/_Norm to peak of all data",     None, self.callback_norm_to_peak_of_all_data, 0, "<ToggleItem>", "gtk-save" ),
		    )


		self.item_factory.create_items(menu_items)


		menubar=self.item_factory.get_widget("<main>")
		menubar.show_all()
		self.pack_start(menubar, False, True, 0)

		self.pack_start(self.toolbar, False, True, 0)	

		pos=0

		self.plot_save = gtk.ToolButton(gtk.STOCK_SAVE)
		self.plot_save.connect("clicked", self.callback_plot_save)
		self.toolbar.add(self.plot_save)
		pos=pos+1

		refresh = gtk.ToolButton(gtk.STOCK_REFRESH)
		refresh.connect("clicked", self.callback_refresh)
		self.toolbar.insert(refresh, pos)
		pos=pos+1

		plot_toolbar = NavigationToolbar(self.canvas, self.win)
		plot_toolbar.show()
		box=gtk.HBox(True, 1)
		box.set_size_request(400,-1)
		box.show()
		box.pack_start(plot_toolbar, True, True, 0)
		tb_comboitem = gtk.ToolItem();
		tb_comboitem.add(box);
		tb_comboitem.show_all()

		self.toolbar.add(tb_comboitem)
		pos=pos+1



		self.toolbar.show_all()


		self.canvas.figure.patch.set_facecolor('white')
		self.canvas.set_size_request(650, 400)
		self.pack_start(self.canvas, True, True, 0)	

		#self.fig.canvas.draw()

		self.canvas.show()

		self.win.connect('key_press_event', self.on_key_press_event)