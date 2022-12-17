import logging
import sqlite3
import typing


class Database:
    logger: logging.Logger

    def __init__(self):
        self.con = sqlite3.connect("db.db")
        self.con.execute("PRAGMA foreign_keys = 1")
        self.cur = self.con.cursor()
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS Faculty(
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        name TEXT NOT NULL,
        dean TEXT NOT NULL,
        office INTEGER NOT NULL
        )
        """
        )
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS StudGroup(
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        name INTEGER,
        FacultyId INTEGER,
        FOREIGN KEY (FacultyId) REFERENCES Faculty(id)
        )
        """
        )
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS Student(
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        GroupId INTEGER NOT NULL,
        Name TEXT NOT NULL,
        Surname TEXT NOT NULL,
        Patronym TEXT NOT NULL,
        DateOfBirth TEXT not null,
        Sex TEXT not null,
        Address TEXT not null,
        FOREIGN KEY (GroupId) REFERENCES StudGroup(id)
        )
        """
        )
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS Benefit(
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        StudentId INTEGER NOT NULL,
        BenefitType TEXT NOT NULL,
        Document TEXT,
        IssueDate TEXT
        )
        """
        )
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS Relative(
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        Name TEXT NOT NULL,
        Surname TEXT NOT NULL,
        Patronym TEXT NOT NULL,
        DateOfBirth TEXT not null,
        Address TEXT not null
        )
        """
        )
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS StudentToRelative(
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        StudentId INTEGER NOT NULL,
        Relationship TEXT NOT NULL,
        RelativeId INTEGER NOT NULL,
        FOREIGN KEY (StudentId) REFERENCES Student(id),
        FOREIGN KEY (RelativeId) REFERENCES Relative(id)
        )
        """
        )
        self.con.commit()

    def get_tables(self) -> list[str, ...]:
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table' and name != 'sqlite_sequence';")
        return self.cur.fetchall() + ["sqlite_master"]

    def get_columns(self, table_name: str) -> list[tuple[str, str], ...]:
        if type(table_name) is tuple:
            table_name = table_name[0]
            print(type(table_name), table_name)
        self.logger.debug(f"Getting columns for {table_name}")
        self.cur.execute(f"PRAGMA table_info({table_name});")
        return [(i[1], (i[2] if i[1] != "id" else "ID")) for i in self.cur.fetchall()]

    def __del__(self):
        self.cur.close()
        self.con.close()

    def get_entries(self, table_name):
        if type(table_name) is tuple:
            table_name = table_name[0]
        self.logger.debug(f"Getting entries for {table_name}")
        self.cur.execute(f"SELECT * FROM {table_name};")
        return self.cur.fetchall()

    def new_entry(self, table_name: str, values: list) -> int:
        self.logger.debug(f"new entry for {table_name} {values=}")
        vals = self.__prepare_values(table_name, values)
        self.logger.debug(f"INSERT INTO {table_name}({', '.join(vals.keys())}) VALUES ({('?, ' * len(vals))[:-2]})")
        self.cur.execute(
            f"INSERT INTO {table_name}({', '.join(vals.keys())}) VALUES ({('?, ' * len(vals))[:-2]})",
            list(vals.values())
        )
        self.con.commit()
        return self.cur.lastrowid

    def edit_entry(self, table_name: str, values: list):
        vals=self.__prepare_values(table_name, values)
        self.logger.debug(f"update entry for {table_name} {vals=}")
        self.cur.execute(f"UPDATE {table_name} SET {' = ?, '.join(vals.keys())} = ? WHERE id = ?", list(vals.values())+[int(values[0])])
        self.con.commit()


    def __prepare_values(self, table_name: str, values: list) -> dict[str, str | int]:
        columns = self.get_columns(table_name)
        assert len(columns) == len(values)
        vals = {}
        for i in range(len(columns)):
            if columns[i][0] == "id":
                continue
            if not values[i]:
                raise ValueError("Not all values are given")
            else:
                if columns[i][1] == "INTEGER":
                    vals[columns[i][0]] = int(values[i])
                else:
                    vals[columns[i][0]] = values[i]
        return vals

    def delete_entry(self,table_name:str, rec_id:int):
        self.cur.execute(f'DELETE FROM {table_name} WHERE id = ?', (rec_id,))
        self.con.commit()

    def sum_of_ids(self, table_name):
        self.cur.execute(f"SELECT COUNT(id) FROM {table_name}")
        return self.cur.fetchall()
