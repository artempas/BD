import logging
import sqlite3
import time
from enum import Enum
from tkinter import *
from tkinter import ttk
from tkinter.messagebox import showerror, showinfo

import logic


class Command(Enum):
    SELECT = 0
    CREATE = 1


class Root(Tk):
    logger: logging.Logger

    def __init__(self, connection: logic.Database):
        super().__init__()
        self.mode = Command.CREATE
        self.connection = connection
        self.logger.debug("Main menu initialized")
        self.buttons_frame = Frame(self)
        self.buttons_frame.grid(row=1, column=1)
        self.db_frame = Frame(self)
        self.db_frame.grid(row=1, column=2)
        self.table_frame = Frame(self.db_frame)
        self.table_frame.pack()
        self.table_buttons_frame = Frame(self.db_frame)
        self.table_buttons_frame.pack()
        self.entry_frame = Frame(self.table_buttons_frame)
        self.entry_frame.pack()
        command_frame = Frame(self.table_buttons_frame)
        command_frame.pack()

        self.table_buttons = [
            Button(self.buttons_frame, text=table, command=lambda temp=table: self.show_table(temp))
            for table in self.connection.get_tables()
        ]
        for btn in self.table_buttons:
            btn.pack()
        scroll_bar = Scrollbar(
            self.table_frame,
            orient=VERTICAL,
        )
        scroll_bar.pack(side=RIGHT, fill=Y)
        self.table = ttk.Treeview(self.table_frame, show="headings", yscrollcommand=scroll_bar.set)
        self.table.pack()
        self.table_entries = []
        self.table_labels = []
        self.logger.debug("Table popup initialized")
        self.new_btn = Button(command_frame, text="New", command=self.new_entry)
        self.new_btn.grid(row=1, column=1)
        self.count_btn = Button(command_frame, text="Number of records", command=self.show_sum)
        self.count_btn.grid(row=1, column=2)
        self.save_btn = Button(command_frame, text="Save", command=self.save_entry)
        self.save_btn.grid(row=2, column=1)
        self.delete_btn = Button(command_frame, text="Delete", command=self.delete_entry)
        self.delete_btn.grid(row=2, column=2)
        self.new_btn.configure(relief="sunken")
        self.new_btn["state"] = "disabled"
        self.show_table(self.table_buttons[0]["text"])
        self.current_table = self.table_buttons[0]["text"]
        self.bind("<<TreeviewSelect>>", self.toggled_focus)

    def show_table(self, table_name: str):
        self.table.delete(*self.table.get_children())
        if type(table_name) is tuple:
            table_name = table_name[0]
        self.current_table = table_name
        assert len(self.table_labels) == len(self.table_entries)
        for i in range(len(self.table_entries)):
            self.table_entries[i].destroy()
            self.table_labels[i].destroy()
        self.table_entries.clear()
        self.table_labels.clear()
        for btn in self.table_buttons:
            if btn["text"] == table_name:
                btn.configure(relief="sunken")
                btn["state"] = "disabled"
            elif btn["state"] == "disabled":
                btn["state"] = "normal"
                btn.configure(relief="raised")
        columns = self.connection.get_columns(table_name)
        self.table["columns"] = tuple(i[0] for i in columns)
        for index, (column, col_type) in enumerate(columns):
            self.table.heading(column, text=column)
            self.table_labels.append(Label(self.entry_frame, text=column))
            self.table_labels[-1].grid(row=2, column=index + 1)
            self.table_entries.append(
                Entry(
                    self.entry_frame,
                    validate="key",
                    validatecommand=(
                        self.register(self.validate_input),
                        "%S",
                        "%P",
                    ),
                )
                if col_type == "INTEGER"
                else Entry(self.entry_frame)
            )
            if col_type == "ID" or self.current_table=='sqlite_master':
                self.table_entries[-1].config(state=DISABLED)
            self.table_entries[-1].grid(row=3, column=index + 1)
        for (i, entry) in enumerate(self.connection.get_entries(table_name)):
            self.table.insert(parent="", index="end", iid=i, text="", values=tuple(entry))
        if self.current_table == "sqlite_master":
            self.save_btn["state"] = "disabled"
            self.delete_btn["state"] = "disabled"
            self.new_btn['state'] = 'disabled'
        else:
            self.new_entry()
            self.save_btn["state"] = "normal"
            self.delete_btn["state"] = "normal"
            self.new_btn['state'] = 'normal'

    def validate_input(self, char, new_val) -> bool:
        # self.logger.debug(f'Validate input: {char=} {new_val=}')
        if not new_val:
            return True
        return char in "01234567890-" and -(2 ** 63) < int(new_val) < 2 ** 63

    def new_entry(self):
        for i in range(len(self.table_entries)):
            disabled = self.table_entries[i]['state'] == DISABLED
            if disabled:
                self.table_entries[i].config(state=NORMAL)
            self.table_entries[i].delete(0, END)
            if disabled:
                self.table_entries[i].config(state=DISABLED)
        self.focus_set()
        self.table.selection_remove(self.table.selection())
        self.mode = Command.CREATE
        self.new_btn.configure(relief="sunken")
        self.new_btn["state"] = "disabled"
        self.delete_btn["state"] = "disabled"

    def save_entry(self):
        try:
            if self.mode == Command.CREATE:
                try:
                    id_ = self.connection.new_entry(self.current_table,
                                                    vals := [entry.get() for entry in self.table_entries])
                except Exception as exc:
                    showerror('Error', str(exc))
                    return
                vals[0] = id_
                new = self.table.insert(parent="", index="end", text="", values=vals)
                self.table.focus(new)
                self.table.selection_set(new)
                self.table.see(new)
            elif self.mode == Command.SELECT:
                try:
                    record = self.connection.edit_entry(self.current_table,
                                                        vals := [entry.get() for entry in self.table_entries])
                except Exception as exc:
                    showerror('Error', str(exc))
                    return
                self.table.item(self.table.focus(), values=vals)
        except sqlite3.IntegrityError as exc:
            showerror("Error", str(exc))
        self.select_entry()

    def select_entry(self):
        self.logger.info("selected new entry")
        # grab record
        selected = self.table.focus()
        # grab record values
        values = self.table.item(selected, "values")
        selected = self.table.focus()
        values = self.table.item(selected, "values")
        if values:
            assert len(values) == len(self.table_entries)
            for i in range(len(self.table_entries)):
                disabled = self.table_entries[i]['state'] == DISABLED
                if disabled:
                    self.table_entries[i].config(state=NORMAL)
                self.table_entries[i].delete(0, END)
                for char in values[i][::-1]:
                    self.table_entries[i].insert(0, char)
                if disabled:
                    self.table_entries[i].config(state=DISABLED)
            self.mode = Command.SELECT
            self.delete_btn["state"] = "normal"
            self.new_btn.configure(relief="raised")
            self.new_btn["state"] = "normal"

    def delete_entry(self):
        self.connection.delete_entry(self.current_table, int(self.table_entries[0].get()))
        self.table.delete(self.table.focus())
        self.new_entry()

    def toggled_focus(self, *args):
        if self.table.focus_get() != self and self.current_table!='sqlite_master':
            self.select_entry()

    def show_sum(self):
        try:
            cnt=self.connection.sum_of_ids(self.current_table)[0][0]
            showinfo('INFO', f"{cnt} records in {self.current_table}")
        except Exception as exc:
            showerror('ERROR', str(exc))
