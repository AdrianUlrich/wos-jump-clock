import json
import tkinter as tk
from tkinter import ttk
from importlib.resources import files

import pandas as pd

from src.data import validate_data
from src.data.constants import *
from src.data.dependencies import depends_on
from upgrade_table import UpgradeTable

# Types
UPGRADE = tuple[str, int]

# Constants
CASTLE_BUFFS = 'Castle Buffs%'
HYENA_SKILL = 'Hyena Skill%'
DOUBLE_TIME = 'Double Time%'
ZINMAN_SKILL = 'Zinman Skill%'
CONSTRUCTION_SPEED = 'Construction Speed%'

SAVEFILE = 'data.json'


def load_data():
    return pd.read_csv(str(files('src').joinpath('data/data.csv')))


class WosJumpClock:
    def __init__(self, root):
        # STATE
        self.root: tk.Tk = root
        validate_data.main()
        self.cost_data: pd.DataFrame = load_data()
        self.archive: pd.DataFrame | None = None
        
        # calculation state
        self.done: set[UPGRADE] = set()
        self.ordered_todo: list[UPGRADE] = []
        self.status: dict[UPGRADE, str] = {}
        
        # GUI
        self.root.title("WOS Jump Clock")
        self.root.state("zoomed")
        
        # WIDGETS
        self.current_level_var = tk.IntVar()
        self.desired_level_var = tk.IntVar()
        self.current_level_combobox = ttk.Combobox(self.root, textvariable=self.current_level_var,
                                                   values=POSSIBLE_LEVELS, width=5)
        self.desired_level_combobox = ttk.Combobox(self.root, textvariable=self.desired_level_var,
                                                   values=POSSIBLE_LEVELS, width=5)
        self.current_level_var.trace_add('write', self._update_all_current_levels)
        self.desired_level_var.trace_add('write', self._update_all_desired_levels)
        self.building_labels = {}
        self.current_level_comboboxes = {}
        self.desired_level_comboboxes = {}
        for building in POSSIBLE_BUILDINGS:
            building_label = tk.Label(self.root, text=building)
            current_level_combobox = ttk.Combobox(self.root, values=POSSIBLE_LEVELS, width=5)
            desired_level_combobox = ttk.Combobox(self.root, values=POSSIBLE_LEVELS, width=5)
            
            self.building_labels[building] = building_label
            self.current_level_comboboxes[building] = current_level_combobox
            self.desired_level_comboboxes[building] = desired_level_combobox
        
        self.save_button = tk.Button(self.root, text='Save all', command=self._save)
        self.load_button = tk.Button(self.root, text='Load', command=self._load)
        self.validate_button = tk.Button(self.root, text='Validate', command=self._clean)
        self.calculate_button = tk.Button(self.root, text='Calculate', command=self._calculate)
        
        self.log_label = tk.Label(self.root, text='Log:')
        self.log_text = tk.Text(self.root, height=1)
        self.log_text.config(state=tk.DISABLED)  # make it read-only
        
        # Table frame
        self.table_frame = UpgradeTable(self)
        
        # LAYOUT (grid)
        nrows = 0
        
        tk.Label(self.root, text='Current Level:').grid(row=nrows, column=1)
        tk.Label(self.root, text='Desired Level:').grid(row=nrows, column=2)
        tk.Label(self.root, text='(optional) Resources:\n(use k/m/b)').grid(row=nrows, column=3, columnspan=2,
                                                                            rowspan=2)
        tk.Label(self.root, text='Bonuses').grid(row=nrows, column=5, columnspan=2)
        
        nrows += 1
        self.current_level_combobox.grid(row=nrows, column=1)
        self.desired_level_combobox.grid(row=nrows, column=2)
        
        nrows += 1
        for i, (building, building_label) in enumerate(self.building_labels.items()):
            building_label.grid(row=i + nrows, column=0, sticky='e')
            self.current_level_comboboxes[building].grid(row=i + nrows, column=1)
            self.desired_level_comboboxes[building].grid(row=i + nrows, column=2)
        
        self.resources = {
            'Meat': tk.Entry(self.root),
            'Wood': tk.Entry(self.root),
            'Coal': tk.Entry(self.root),
            'Iron': tk.Entry(self.root),
            'Crystal': tk.Entry(self.root),
            'RFC': tk.Entry(self.root),
            'Construction Speedups (min)': tk.Entry(self.root),
            'General Speedups (min)': tk.Entry(self.root),
        }
        for i, (resource, entry) in enumerate(self.resources.items()):
            tk.Label(self.root, text=resource).grid(row=i + nrows, column=3, sticky='e')
            entry.grid(row=i + nrows, column=4)
        
        self.bonuses = {
            CONSTRUCTION_SPEED: tk.Entry(self.root, width=5),
            ZINMAN_SKILL: ttk.Combobox(self.root, values=[str(x) for x in range(0, 18, 3)], width=5),
            DOUBLE_TIME: ttk.Combobox(self.root, values=['0', '20'], width=5),
            HYENA_SKILL: ttk.Combobox(self.root, values=['0', '5', '7', '9', '12', '15'], width=5),
            CASTLE_BUFFS: ttk.Combobox(self.root, values=['0'], width=5),
        }
        for i, (bonus, entry) in enumerate(self.bonuses.items()):
            tk.Label(self.root, text=bonus).grid(row=i + nrows, column=5, sticky='e')
            entry.grid(row=i + nrows, column=6)
        
        i = len(self.bonuses) + 1
        self.save_button.grid(row=i + nrows, column=5, sticky='e')
        self.load_button.grid(row=i + nrows, column=6, sticky='ew')
        self.validate_button.grid(row=i + nrows + 1, column=5, sticky='e')
        self.calculate_button.grid(row=i + nrows + 1, column=6, sticky='ew')
        
        nrows += max(len(self.building_labels), len(self.resources))
        
        # one separator row
        ttk.Separator(self.root, orient='horizontal').grid(row=nrows, column=0, columnspan=7, sticky='ew')
        nrows += 1
        
        self.log_label.grid(row=nrows, column=0, sticky='e')
        self.log_text.grid(row=nrows, column=1, columnspan=6, sticky='ew')
        nrows += 1
        
        ttk.Separator(self.root, orient='horizontal').grid(row=nrows, column=0, columnspan=7, sticky='ew')
        nrows += 1
        
        # Table layout
        self.table_frame.grid(row=nrows, column=0, columnspan=7, sticky='ew')
        
        # BINDINGS
        self.root.bind("<Escape>", self._exit)
        
        # ACTIONS
        self._load()
    
    def _log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, message)
        self.log_text.config(state=tk.DISABLED)
    
    def _save(self):
        # get all values into a dictionary
        data = {}
        for building in POSSIBLE_BUILDINGS:
            data[building] = {'current_level': self.current_level_comboboxes[building].get(),
                              'desired_level': self.desired_level_comboboxes[building].get()}
        
        for resource, entry in self.resources.items():
            data[resource] = entry.get()
        
        for bonus, entry in self.bonuses.items():
            data[bonus] = entry.get()
        
        data['todo'] = self.ordered_todo
        data['status'] = [[building, level, status] for (building, level), status in self.status.items()]
        
        # save to json file
        with open(SAVEFILE, 'w') as f:
            json.dump(data, f, indent=4)
        
        # also archive the data (timestamped) for later stats
        if self.archive is None:
            self.archive = pd.DataFrame(columns=['timestamp', 'key', 'value'])
        now = pd.Timestamp.now()
        for key, value in data.items():
            row = {'timestamp': now, 'key': key, 'value': value if isinstance(value, str)
            else value['current_level'] if isinstance(value, dict) else f'ERROR {value}'}
            self.archive = pd.concat([self.archive, pd.DataFrame(row, index=[0])], ignore_index=True)
        
        self.archive.to_csv('archive.csv', index=False)
        
        self._log(f'Saved {len(data)} values to save file')
    
    def _load(self):
        # load from json file
        try:
            with open(SAVEFILE, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            self._log('No save file found')
            return
        
        # set all values
        for building in POSSIBLE_BUILDINGS:
            self.current_level_comboboxes[building].set(data[building]['current_level'])
            self.desired_level_comboboxes[building].set(data[building]['desired_level'])
        
        for resource, entry in self.resources.items():
            entry.delete(0, tk.END)
            entry.insert(0, data[resource])
        
        for bonus, entry in self.bonuses.items():
            if bonus == CONSTRUCTION_SPEED:
                entry.delete(0, tk.END)
                entry.insert(0, data[bonus])
            else:
                entry.set(data[bonus])
        
        self.ordered_todo = data.get('todo', [])
        self.status = {(building, level): status
                       for building, level, status in data.get('status', [])}
        
        # load the csv archive, or create it if it doesn't exist
        try:
            self.archive = pd.read_csv('archive.csv')
        except FileNotFoundError:
            self.archive = pd.DataFrame(columns=['timestamp', 'key', 'value'])
            self.archive.to_csv('archive.csv', index=False)
        
        self._log(f'Loaded {len(data)} values from data.json')
    
    def _clean(self):
        """
        Clean up the entries to a standard format.
        """
        # clean up resources (all should be numbers, in k/m/b format)
        for entry in self.resources.values():
            txt = entry.get()
            txt = txt.replace(',', '')
            txt = txt.replace('k', 'K', 1)
            txt = txt.replace('m', 'M', 1)
            txt = txt.replace('b', 'B', 1)
            entry.delete(0, tk.END)
            entry.insert(0, txt)
        
        # clean up bonuses (all should be percentages)
        for entry in self.bonuses.values():
            txt = entry.get()
            txt = txt.replace('%', '')
            try:
                n = float(txt)
            except ValueError:
                n = 0
            entry.delete(0, tk.END)
            entry.insert(0, str(n).rstrip('0').rstrip('.'))
        
        # cleanup current and desired levels
        for building in POSSIBLE_BUILDINGS:
            current_box = self.current_level_comboboxes[building]
            desired_box = self.desired_level_comboboxes[building]
            if current_box.get() == '':
                current_box.set('24')
            if desired_box.get() == '' or int(desired_box.get()) < int(current_box.get()):
                desired_box.set(current_box.get())
        
        self.done = {(building, int(current_box.get())) for building, current_box in
                     self.current_level_comboboxes.items()}
        
        # use the dependecies to calculate the missing upgrades
        todo = [(building, int(desired_box.get()))
                for building, desired_box in self.desired_level_comboboxes.items()
                if (building, int(desired_box.get())) not in self.done]
        
        # only add to the ordered_todo if all dependencies are met or already in ordered_todo
        self.ordered_todo.clear()
        while todo:
            building, level = todo.pop()
            not_missing = self.done | set(self.ordered_todo)
            if (building, level) in not_missing:
                continue
            deps = set(depends_on(building, level))
            missing = deps - not_missing
            if not missing:
                self.ordered_todo.append((building, level))
                # update desires
                if level > int(self.desired_level_comboboxes[building].get()):
                    self.desired_level_comboboxes[building].set(str(level))
            else:
                todo.append((building, level))
                todo.extend(missing)
        
        print(' '.join(f'{building[0]}{level}' for building, level in self.ordered_todo))
        
        self._log('Cleaned up entries')
    
    def _calculate(self):
        """
        This is the meat and potatoes of the program.
        Here we generate the full upgrade plan, and initialize The
        Clock (tm).
        Clean already prepared the ordered_todo list, so here we take care of costs.
        """
        self._clean()
        self.table_frame.update_table()
    
    def _update_all_current_levels(self, *_):
        current_level = self.current_level_var.get()
        for combobox in self.current_level_comboboxes.values():
            combobox.set(current_level)
    
    def _update_all_desired_levels(self, *_):
        desired_level = self.desired_level_var.get()
        for combobox in self.desired_level_comboboxes.values():
            combobox.set(desired_level)
    
    def _exit(self, _):
        self.root.quit()
    
    @property
    def construction_speed(self):
        """
        The construction speed bonus, as a decimal. This value is usually bigger than 1.
        An input of 50% would be 1.5 speed, meaning a factor of 2/3
        """
        return 1 / (1 + (float(self.bonuses[CONSTRUCTION_SPEED].get().rstrip('%')) / 100))
    
    @property
    def zinman_skill(self):
        """
        Zinman's skill also modifies the duration of the upgrade, but it is already counted in the construction speed.
        This is the resource cost reduction.
        12% would be 0.88, changing a 1M meat cost to 880k meat.
        """
        return 1 - (float(self.bonuses[ZINMAN_SKILL].get()) / 100)
    
    @property
    def bonus_speed(self):
        """
        As opposed to construction_speed, bonuses directly modify the duration of the upgrade.
        So a bonus of 20% would be 0.8
        Two such bonuses would be 0.8 * 0.8 = 0.64
        """
        double_time = 1 - (float(self.bonuses[DOUBLE_TIME].get().rstrip('%')) / 100)
        hyena_skill = 1 - (float(self.bonuses[HYENA_SKILL].get().rstrip('%')) / 100)
        castle_buffs = 1 - (float(self.bonuses[CASTLE_BUFFS].get().rstrip('%')) / 100)
        return double_time * hyena_skill * castle_buffs


def main():
    root = tk.Tk()
    _ = WosJumpClock(root)
    root.mainloop()


if __name__ == "__main__":
    main()
