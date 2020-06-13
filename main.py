import kivy
import pickle
import time

from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty

from processentry import generate_pdf, email_file, add_entry_to_xlsx

################################################################################

class InfoPopup(Popup):
    msg = StringProperty()

class ConfirmPopup(Popup):
    msg = StringProperty()
    form_widget = ObjectProperty()


class DrawingPad(Widget):
    def on_touch_down(self, touch):
        with self.canvas:
            Color(0, 0, 0)
            if self.collide_point(*touch.pos):
                self.drawing = True
                touch.ud['line'] = Line(points = (touch.x, touch.y), width = 2)
            else:
                self.drawing = False

    def on_touch_move(self, touch):
        if self.drawing and self.collide_point(*touch.pos):
            touch.ud['line'].points += (touch.x, touch.y)
        else:
            self.drawing = False


class Field(BoxLayout):
    def validate(self, show_popup = True):
        if self.input.text == '' and self.required:
            error = 'This field cannot be left empty'
        elif self.type == 'printable':
            error = None
        else:
            error = Field.types[self.type](self)

        if error is None:
            self.label.color = [1, 1, 1, 1]
            return True
        else:
            self.label.color = [1, 0, 0, 1]
            if show_popup:
                InfoPopup(title = 'Input error', msg = error).open()
            return False

    def _val_alpha(self):
        for char in self.input.text:
            if not char.isalpha() and char not in ' .':
                return 'Only alphabets, spaces and periods are allowed'
        return None

    def _val_numeric(self):
        if self.input.text.isnumeric():
            return None
        else:
            return 'Only numbers are allowed'

    def _val_phnum(self):
        for char in self.input.text:
            if not char.isnumeric() and char not in '+ -()':
                return 'Only numbers, spaces, signs, and brackets are allowed'
        return None

    def _val_email(self):
        split = self.input.text.split('@')
        if len(split) == 2 and split[1].count('.') >= 1:
            return None
        else:
            return 'You must enter a valid email address'

    types = {'alpha': _val_alpha, 'numeric': _val_numeric,
             'phnum': _val_phnum, 'email': _val_email}


class FormScreen(Screen):
    def load(self):
        self.add_widget(Form())

    def unload(self):
        self.clear_widgets()


class Form(BoxLayout):
    def process_form(self):
        inputs = {}
        for widget in self.walk():
            if type(widget) is Field:
                if not widget.validate(show_popup = False):
                    msg = f'Please correctly fill {widget.label.text[ :-1]}'
                    InfoPopup(title = 'Input error', msg = msg).open()
                    return
                else:
                    inputs[widget.label.text[ :-1]] = widget.input.text
            elif type(widget) is TextInput and type(widget.parent) is not Field:
                inputs['Notes'] = widget.text
            elif type(widget) is DrawingPad:
                widget.export_to_png('data/signature.png')
        self.inputs = inputs
        self.confirm_submit()

    def confirm_submit(self):
        title = 'Confirm submission'
        msg = 'Are you sure you want to submit the form?'
        ConfirmPopup(title = title, msg = msg, form_widget = self).open()

    def submit_form(self):
        with open('data/counter', 'rb') as file:
            entry_num = pickle.load(file) + 1

        with open('data/counter', 'wb') as file:
            pickle.dump(entry_num, file)

        entry_num = str(entry_num)

        pdf = generate_pdf(self.inputs, entry_num)
        pdf.output(f'data/archive/{entry_num}.pdf', 'F')

        filename = f'data/archive/{entry_num}.pdf'
        subject = f'New entry #{entry_num}'
        Thread(target = email_file, args = (filename, subject)).start()

        add_entry_to_xlsx(self.inputs, entry_num)

        msg = 'Your entry was successfully submitted'
        InfoPopup(title = 'Success', msg = msg).open()



################################################################################

class HomeScreen(Screen):
    def update_clock(self, *args):
        self.clock.text = time.strftime('%H:%M:%S')

################################################################################

class Manager(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        home_screen = HomeScreen(name = 'home')
        form_screen = FormScreen(name = 'form')
        self.add_widget(home_screen)
        self.add_widget(form_screen)
        Clock.schedule_interval(home_screen.update_clock, 1)

    def on_current(self, instance, value):
        if self.current == 'home':
            self.transition.direction = 'right'
        else:
            self.transition.direction = 'left'
        super().on_current(instance, value)


class CheckInApp(App):
    def build(self):
        return Manager()


if __name__ == '__main__':
    CheckInApp().run()
