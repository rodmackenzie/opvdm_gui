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

import pygtk
pygtk.require('2.0')
import gtk
import sys
import math
import random
from layer_widget import layer_widget
from util import read_xyz_data
import os
from cal_path import get_phys_path
from inp import inp_load_file
from inp import inp_search_token_value
from util import str2bool

class tab_main(gtk.VBox):

	def update(self,object):
		self.darea.queue_draw()

	def init(self,tooltips):
		self.sun=1
		main_hbox=gtk.HBox()
		self.darea = gtk.DrawingArea()
		self.darea.connect("expose-event", self.expose)
		#darea.show()

		self.frame=layer_widget(tooltips)
		main_hbox.pack_start(self.frame, False, False, 0)
		main_hbox.pack_start(self.darea, True, True, 0)

		self.frame.connect("refresh", self.update)

		self.add(main_hbox)
		self.show_all()

	def draw_photon(self,x_start,y_start):
		x=x_start
		y=y_start
		self.cr.set_source_rgb(0,1.0,0.0)
		self.cr.move_to(x, y)
		self.cr.set_line_width(2)
		while (y<y_start+101):
			self.cr.line_to(x+math.sin((y_start-y)/4)*10, y)
			y=y+0.1
		self.cr.stroke()

		self.cr.line_to(x+10, y)
		self.cr.line_to(x, y+20)
		self.cr.line_to(x-10, y)
		self.cr.fill()
		#optical_mode_file
		

		#self.cr.restore()

	def draw_box(self,x,y,z,r,g,b,model):
		text=model[1]
		active_layer=str2bool(model[2])
		self.cr.set_source_rgb(r,g,b)

		points=[(x,y), (x+200,y), (x+200,y+z), (x,y+z)]
		print points
		self.cr.move_to(x, y)
		for px,py in points:
			self.cr.line_to(px, py)
		self.cr.fill()

		if active_layer==True:
			points=[(x+285,y-60), (x+295,y-60), (x+295,y+z-60), (x+285,y+z-60)]
			print points
			self.cr.set_source_rgb(0.0,0.0,0.7)
			self.cr.move_to(points[0][0], points[0][1])
			for px,py in points:
				self.cr.line_to(px, py)
			self.cr.fill()

		r=r*0.5
		g=g*0.5
		b=b*0.5
		self.cr.set_source_rgb(r,g,b)

		points=[(x+200,y-0),(x+200,y+z), (x+200+80,y-60+z),(x+200+80,y-60)]
		print points
		self.cr.move_to(points[0][0], points[0][1])
		for px,py in points:
			self.cr.line_to(px, py)
		self.cr.fill()

		r=r*0.5
		g=g*0.5
		b=b*0.5
		self.cr.set_source_rgb(r,g,b)

		points=[(x,y),(x+200,y), (x+200+80,y-60), (x+100,y-60)]
		self.cr.move_to(points[0][0], points[0][1])
		print points
		self.cr.move_to(x, y)
		for px,py in points:
			self.cr.line_to(px, py)
		self.cr.fill()
		self.cr.set_font_size(14)
		self.cr.move_to(x+200+80+20, y-60+z/2)
		self.cr.show_text(text)

	def draw_mode(self,x_start,y_start,z_size):
		t=[]
		s=[]
		z=[]
		x=x_start
		y=y_start
		self.cr.set_source_rgb(0.2,0.2,0.2)
		if read_xyz_data(t,s,z,os.path.join(os.getcwd(),"light_dump","light_1d_photons_tot_norm.dat"))==True:
			self.cr.move_to(x-s[0]*40, y)
			self.cr.set_line_width(5)
			array_len=len(t)

			for i in range(0,array_len):
					self.cr.line_to(x-s[i]*40, y_start+(z_size*i/array_len))

		self.cr.stroke()

	def set_sun(self,sun):
		self.sun=sun

	def draw(self,model):
		tot=0
		for i in range(0,len(model)):
			tot=tot+float(model[i][0])

		pos=0.0
		l=len(model)-1
		lines=[]

		for i in range(0,len(model)):
			thick=200.0*float(model[l-i][0])/tot
			pos=pos+thick
			print "Draw"
			path=os.path.join(get_phys_path(),model[l-i][1],"mat.inp")

			if inp_load_file(lines,path)==True:
				red=float(inp_search_token_value(lines, "#Red"))
				green=float(inp_search_token_value(lines, "#Green"))
				blue=float(inp_search_token_value(lines, "#Blue"))
			else:
				red=0.0
				green=0.0
				blue=0.0
			self.draw_box(200,450.0-pos,thick*0.9,red,green,blue,model[l-i])
		step=50.0

		lines=[]
		if inp_load_file(lines,os.path.join(os.getcwd(),"light.inp"))==True:
			self.sun=float(inp_search_token_value(lines, "#Psun"))

		if self.sun<=0.01:
			step=200
		elif self.sun<=0.1:
			step=100
		elif self.sun<=1.0:
			step=50
		elif self.sun<=10.0:
			step=10
		else:
			step=5.0
		if self.sun!=0:
			for x in range(0,200,step):
				self.draw_photon(270+x,50)

		self.draw_mode(200,250,200)

	def expose(self, widget, event):

		self.cr = widget.window.cairo_create()

		self.cr.set_line_width(9)
		self.cr.set_source_rgb(0.7, 0.2, 0.0)
		        
		w = self.allocation.width
		h = self.allocation.height

		#self.cr.translate(w/2, h/2)

		self.draw(self.frame.model)

