# -*- coding: utf-8 -*-

from __future__ import with_statement
import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import *  # noqa
from _Framework.ButtonElement import ButtonElement
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from ConfigurableButtonElement import ConfigurableButtonElement
from MainSelectorComponent import MainSelectorComponent
from M4LInterface import M4LInterface
import Settings
from Skin import Skin

DO_COMBINE = Live.Application.combine_apcs()  # requires 8.2 & higher


class Launchpad(ControlSurface):

	""" Script for Novation's Launchpad Controller """

	def __init__(self, c_instance):
		live = Live.Application.get_application()
		self._live_major_version = live.get_major_version()
		self._live_minor_version = live.get_minor_version()
		self._live_bugfix_version = live.get_bugfix_version()
		self._mk2_rgb = Settings.DEVICE=='Launchpad mk2'
		if self._mk2_rgb:
			self._skin = Skin('launchpad mk2')
			self._side_notes = (89, 79, 69, 59, 49, 39, 29, 19)
			self._drum_notes = (20, 30, 31, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126)
		else:
			self._skin = Skin('launchpad')
			self._side_notes = (8, 24, 40, 56, 72, 88, 104, 120)
			self._drum_notes = (41, 42, 43, 44, 45, 46, 47, 57, 58, 59, 60, 61, 62, 63, 73, 74, 75, 76, 77, 78, 79, 89, 90, 91, 92, 93, 94, 95, 105, 106, 107)
			
			
		ControlSurface.__init__(self, c_instance)
	
	
		with self.component_guard():
			self._suppress_send_midi = True
			self._suppress_session_highlight = True

			is_momentary = True
			if self._mk2_rgb:
				self._suggested_input_port = ("Launchpad", "Launchpad Mini", "Launchpad S")
				self._suggested_output_port = ("Launchpad", "Launchpad Mini", "Launchpad S")
			else:
				self._suggested_input_port = "Launchpad MK2"
				self._suggested_output_port = "Launchpad MK2"				
			self._control_is_with_automap = False
			self._user_byte_write_button = ButtonElement(is_momentary, MIDI_CC_TYPE, 0, 16)
			self._user_byte_write_button.name = 'User_Byte_Button'
			self._user_byte_write_button.send_value(1)
			self._user_byte_write_button.add_value_listener(self._user_byte_value)
			self._wrote_user_byte = False
			self._challenge = Live.Application.get_random_int(0, 400000000) & 2139062143
			matrix = ButtonMatrixElement()
			matrix.name = 'Button_Matrix'
			for row in range(8):
				button_row = []
				for column in range(8):
					if self._mk2_rgb:
						# for mk2 buttons are assigned "top to bottom"
 						midi_note = (81 - (10 * row)) + column
					else:
						midi_note = row * 16 + column
					button = ConfigurableButtonElement(is_momentary, MIDI_NOTE_TYPE, 0, midi_note, self._skin.off)
					button.name = str(column) + '_Clip_' + str(row) + '_Button'
					button_row.append(button)

				matrix.add_row(tuple(button_row))

			self._config_button = ButtonElement(is_momentary, MIDI_CC_TYPE, 0, 0, optimized_send_midi=False)
			self._config_button.add_value_listener(self._config_value)
			top_buttons = [ConfigurableButtonElement(is_momentary, MIDI_CC_TYPE, 0, 104 + index, self._skin.off) for index in range(8)]
			side_buttons = [ConfigurableButtonElement(is_momentary, MIDI_NOTE_TYPE, 0, self._side_notes[index], self._skin.off) for index in range(8)]
			top_buttons[0].name = 'Bank_Select_Up_Button'
			top_buttons[1].name = 'Bank_Select_Down_Button'
			top_buttons[2].name = 'Bank_Select_Left_Button'
			top_buttons[3].name = 'Bank_Select_Right_Button'
			top_buttons[4].name = 'Session_Button'
			top_buttons[5].name = 'User1_Button'
			top_buttons[6].name = 'User2_Button'
			top_buttons[7].name = 'Mixer_Button'
			side_buttons[0].name = 'Vol_Button'
			side_buttons[1].name = 'Pan_Button'
			side_buttons[2].name = 'SndA_Button'
			side_buttons[3].name = 'SndB_Button'
			side_buttons[4].name = 'Stop_Button'
			side_buttons[5].name = 'Trk_On_Button'
			side_buttons[6].name = 'Solo_Button'
			side_buttons[7].name = 'Arm_Button'
			self._osd = M4LInterface()
			self._osd.name = "OSD"
			self._selector = MainSelectorComponent(matrix, tuple(top_buttons), tuple(side_buttons), self._config_button, self._osd, self)
			self._selector.name = 'Main_Modes'
			self._do_combine()
			for control in self.controls:
				if isinstance(control, ConfigurableButtonElement):
					control.add_value_listener(self._button_value)

			self.set_highlighting_session_component(self._selector.session_component())
			self._suppress_session_highlight = False

			self.log_message("LaunchPad95 Loaded !")

	def disconnect(self):
		self._suppress_send_midi = True
		for control in self.controls:
			if isinstance(control, ConfigurableButtonElement):
				control.remove_value_listener(self._button_value)
		self._do_uncombine()
		self._selector = None
		self._user_byte_write_button.remove_value_listener(self._user_byte_value)
		self._config_button.remove_value_listener(self._config_value)
		ControlSurface.disconnect(self)
		self._suppress_send_midi = False
		if self._mk2_rgb:
			self._send_midi((240, 0, 32, 41, 2, 24, 64, 247))
			# launchpad mk2 needs disconnect string sent			
		self._config_button.send_value(32)
		self._config_button.send_value(0)
		self._config_button = None
		self._user_byte_write_button.send_value(0)
		self._user_byte_write_button = None

	_active_instances = []

	#def highlighting_session_component(self):
	#	" Return the session component showing the ring in Live session "
	#	return self._selector.session_component()

	def _combine_active_instances():
		support_devices = False
		for instance in Launchpad._active_instances:
			support_devices |= (instance._device_component != None)
		offset = 0
		for instance in Launchpad._active_instances:
			instance._activate_combination_mode(offset, support_devices)
			offset += instance._selector._session.width()

	_combine_active_instances = staticmethod(_combine_active_instances)

	def _activate_combination_mode(self, track_offset, support_devices):
		if(Settings.STEPSEQ__LINK_WITH_SESSION):
			self._selector._stepseq.link_with_step_offset(track_offset)
		if(Settings.SESSION__LINK):
			self._selector._session.link_with_track_offset(track_offset)

	def _do_combine(self):
		if (DO_COMBINE and (self not in Launchpad._active_instances)):
			Launchpad._active_instances.append(self)
			Launchpad._combine_active_instances()

	def _do_uncombine(self):
		if self in Launchpad._active_instances:
			Launchpad._active_instances.remove(self)
			if(Settings.SESSION__LINK):
				self._selector._session.unlink()
			if(Settings.STEPSEQ__LINK_WITH_SESSION):
				self._selector._stepseq.unlink()
			Launchpad._combine_active_instances()

	def refresh_state(self):
		ControlSurface.refresh_state(self)
		self.schedule_message(5, self._update_hardware)

	def handle_sysex(self, midi_bytes):
		if self._mk2_rgb:
			# mk2 has different challenge and params
			if len(midi_bytes) == 10:
				if midi_bytes[:7] == (240, 0, 32, 41, 2, 24, 64):
					response = long(midi_bytes[7])
					response += long(midi_bytes[8]) << 8
					if response == Live.Application.encrypt_challenge2(self._challenge):
						# self.log_message("Challenge Response ok")
						self._suppress_send_midi = False
						self.set_enabled(True)
		else:
			if len(midi_bytes) == 8:
				if midi_bytes[1:5] == (0, 32, 41, 6):
					response = long(midi_bytes[5])
					response += long(midi_bytes[6]) << 8
					if response == Live.Application.encrypt_challenge2(self._challenge):
						self._suppress_send_midi = False
						self.set_enabled(True)

	def build_midi_map(self, midi_map_handle):
		ControlSurface.build_midi_map(self, midi_map_handle)
		if self._selector.mode_index == 1:
			if self._selector._sub_mode_index[self._selector._mode_index] > 0:  # disable midi map rebuild for instrument mode to prevent light feedback errors
				new_channel = self._selector.channel_for_current_mode()
				# self.log_message(str(new_channel))
				for note in self.drum_notes:
					self._translate_message(MIDI_NOTE_TYPE, note, 0, note, new_channel)

	def _send_midi(self, midi_bytes, optimized=None):
		sent_successfully = False
		if not self._suppress_send_midi:
			sent_successfully = ControlSurface._send_midi(self, midi_bytes, optimized=optimized)
		return sent_successfully

	def _update_hardware(self):
		self._suppress_send_midi = False
		self._wrote_user_byte = True
		self._user_byte_write_button.send_value(1)
		self._suppress_send_midi = True
		self.set_enabled(False)
		self._suppress_send_midi = False
		self._send_challenge()

	def _send_challenge(self):
		if self._mk2_rgb:
			challenge_bytes = tuple([ self._challenge >> 8 * index & 127 for index in xrange(4) ])
			self._send_midi((240, 0, 32, 41, 2, 24, 64) + challenge_bytes + (247,))
		else:
			for index in range(4):
				challenge_byte = self._challenge >> 8 * index & 127
				self._send_midi((176, 17 + index, challenge_byte))
		

	def _user_byte_value(self, value):
		assert (value in range(128))
		if not self._wrote_user_byte:
			enabled = (value == 1)
			self._control_is_with_automap = not enabled
			self._suppress_send_midi = self._control_is_with_automap
			if not self._control_is_with_automap:
				for control in self.controls:
					if isinstance(control, ConfigurableButtonElement):
						control.set_force_next_value()

			self._selector.set_mode(0)
			self.set_enabled(enabled)
			self._suppress_send_midi = False
		else:
			self._wrote_user_byte = False

	def _button_value(self, value):
		assert value in range(128)

	def _config_value(self, value):
		assert value in range(128)

	def _set_session_highlight(self, track_offset, scene_offset, width, height, include_return_tracks):
		if not self._suppress_session_highlight:
			ControlSurface._set_session_highlight(self, track_offset, scene_offset, width, height, include_return_tracks)
