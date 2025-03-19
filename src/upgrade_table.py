import datetime
import tkinter as tk
from math import floor, ceil

import pandas as pd

from src.data.constants import *
from src.data.dependencies import depends_on
from src.time_conversions import from_minutes, to_minutes

EXPLANATION = """
        This table shows the cost of upgrading buildings to the next level. The cost is in terms of Meat, Wood, Stone, Iron, and Crystal, modified by Zinman's skill.
        Duration is the result of the formula: base_duration * (1/(1+construction_speed)) * (1-bonus_1) * ...
        Status will be modifiable if the upgrade is available. To start an upgrade, simply enter the current indicated ETA (XdYhZm) in the field.
        GREEN: Done, RED: Locked, WHITE: Available, BLUE: In Progress
        """

HEADERS = [COLUMN_BUILDING, COLUMN_LEVEL, COLUMN_MEAT, COLUMN_WOOD, COLUMN_COAL, COLUMN_IRON, COLUMN_CRYSTAL,
           COLUMN_RFC, 'Base Duration', COLUMN_DURATION, 'Status', 'Confirm Status', 'ETA']


def to_units(rss: str) -> int:
    try:
        # if already a number, return it
        return ceil(float(rss))
    except ValueError:
        pass
    if rss[-1] in ['k', 'K']:
        return ceil(float(rss[:-1]) * 1e3)
    elif rss[-1] in ['m', 'M']:
        return ceil(float(rss[:-1]) * 1e6)
    elif rss[-1] in ['b', 'B']:
        return ceil(float(rss[:-1]) * 1e9)
    else:
        raise ValueError(f'RSS value {rss} not understood')


class UpgradeTable(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.cost_data = parent.cost_data
        
        # WIDGETS
        self.explanation = tk.Label(self, text=EXPLANATION, justify='left')
        self.headers = {header: tk.Label(self, text=header, borderwidth=1, relief="solid") for header in HEADERS}
        self.upgrade_widgets = {}
        self.refresh_button = tk.Button(self, text='↻', command=self.update_table)
        
        # LAYOUT
        self.explanation.grid(row=0, column=0, columnspan=1 + len(HEADERS), sticky=tk.SE)
        self.refresh_button.grid(row=1, column=0)
        [self.headers[h].grid(row=1, column=col + 1, sticky="nsew") for col, h in enumerate(HEADERS)]
    
    def update_table(self):
        ordered_todo = self.parent.ordered_todo
        status = self.parent.status
        done = self.parent.done
        
        # if any widgets are missing, we need to recreate the whole table
        if any([upgrade not in self.upgrade_widgets for upgrade in ordered_todo]):
            [widget.destroy()
             for widgets in self.upgrade_widgets.values()
             for widget in widgets.values()]
            self.upgrade_widgets = {}
        
        for i, upgrade in enumerate(ordered_todo):
            # we can assume the widget is either already in the right place, or not there at all
            building, level = upgrade
            if upgrade in status:
                # just update the status
                self.update_status(upgrade)
                continue
            
            row = self.cost_data[(self.cost_data['Building'] == building) & (self.cost_data['Level'] == level)]
            meat = row[COLUMN_MEAT].values[0]
            wood = row[COLUMN_WOOD].values[0]
            stone = row[COLUMN_COAL].values[0]
            iron = row[COLUMN_IRON].values[0]
            crystal = row[COLUMN_CRYSTAL].values[0]
            rfc = row[COLUMN_RFC].values[0]
            base_duration = row[COLUMN_DURATION].values[0]
            minutes = row[COLUMN_MINUTES].values[0]
            
            # rss cost reduction
            meat = ceil(to_units(meat) * self.parent.zinman_skill)
            wood = ceil(to_units(wood) * self.parent.zinman_skill)
            stone = ceil(to_units(stone) * self.parent.zinman_skill)
            iron = ceil(to_units(iron) * self.parent.zinman_skill)
            
            # speed
            discounted_minutes = minutes * self.parent.construction_speed * self.parent.bonus_speed
            duration = from_minutes(ceil(discounted_minutes))
            
            widgets = {
                'index_label': tk.Label(self, text=str(i + 1)),
                'building_label': tk.Label(self, text=building),
                'level_label': tk.Label(self, text=level),
                'meat_label': tk.Label(self, text=meat),
                'wood_label': tk.Label(self, text=wood),
                'stone_label': tk.Label(self, text=stone),
                'iron_label': tk.Label(self, text=iron),
                'crystal_label': tk.Label(self, text=crystal),
                'rfc_label': tk.Label(self, text=rfc),
                'base_duration_label': tk.Label(self, text=base_duration),
                'duration_label': tk.Label(self, text=duration),
                'status': tk.Entry(self),
                'confirm_status': tk.Button(self, text="Confirm", command=self._confirm_status(upgrade)),
                'eta': tk.Label(self),
            }
            assert len(widgets) == len(HEADERS) + 1, f'{len(widgets)=} != {len(HEADERS)=}'
            self.upgrade_widgets[upgrade] = widgets
            self.update_status(upgrade)
            
            # LAYOUT
            widgets['index_label'].grid(row=i + 2, column=0)
            widgets['building_label'].grid(row=i + 2, column=1)
            widgets['level_label'].grid(row=i + 2, column=2)
            widgets['meat_label'].grid(row=i + 2, column=3)
            widgets['wood_label'].grid(row=i + 2, column=4)
            widgets['stone_label'].grid(row=i + 2, column=5)
            widgets['iron_label'].grid(row=i + 2, column=6)
            widgets['crystal_label'].grid(row=i + 2, column=7)
            widgets['rfc_label'].grid(row=i + 2, column=8)
            widgets['base_duration_label'].grid(row=i + 2, column=9)
            widgets['duration_label'].grid(row=i + 2, column=10)
            widgets['status'].grid(row=i + 2, column=11)
            widgets['confirm_status'].grid(row=i + 2, column=12)
            widgets['eta'].grid(row=i + 2, column=13)
    
    def _confirm_status(self, upgrade):
        def confirm():
            widget_active = self.upgrade_widgets[upgrade]['status'].cget('state')
            if widget_active == 'disabled':
                return
            status = self.upgrade_widgets[upgrade]['status'].get()
            minutes = to_minutes(status)
            self.parent.status.setdefault(upgrade, {})
            self.parent.status[upgrade]['minutes'] = minutes
            self.parent.status[upgrade]['Confirmed Time'] = datetime.datetime.now().timestamp()
            self.update_status(upgrade)
        
        return confirm
    
    def update_status(self, upgrade):
        # no matter what, check the dependencies, and update the activity of the status widget and confirm button
        building, level = upgrade
        done = self.parent.done
        if upgrade in done:
            self.upgrade_widgets[upgrade]['status'].config(state='normal')
            self.upgrade_widgets[upgrade]['status'].config(disabledbackground='green')
            self.upgrade_widgets[upgrade]['status'].delete(0, 'end')
            self.upgrade_widgets[upgrade]['status'].insert(0, 'Done')
            self.upgrade_widgets[upgrade]['status'].config(state='disabled')
            self.upgrade_widgets[upgrade]['confirm_status'].config(state='disabled')
            return
        if any([dep not in done for dep in (depends_on(building, level))]):
            self.upgrade_widgets[upgrade]['status'].config(state='normal')
            self.upgrade_widgets[upgrade]['status'].config(disabledbackground='red')
            self.upgrade_widgets[upgrade]['status'].delete(0, 'end')
            self.upgrade_widgets[upgrade]['status'].insert(0, 'Locked')
            self.upgrade_widgets[upgrade]['status'].config(state='disabled')
            self.upgrade_widgets[upgrade]['confirm_status'].config(state='disabled')
            return
        
        # available
        self.upgrade_widgets[upgrade]['status'].config(state='normal')
        self.upgrade_widgets[upgrade]['confirm_status'].config(state='normal')
        
        status = self.parent.status
        if upgrade not in status:
            # Let user input the ETA from ingame timer
            self.upgrade_widgets[upgrade]['status'].config(bg='white')
            self.upgrade_widgets[upgrade]['status'].delete(0, 'end')
            return
        
        # there is a confirmed status
        self.upgrade_widgets[upgrade]['status'].config(bg='blue')
        conf = datetime.datetime.fromtimestamp(self.parent.status[upgrade]['Confirmed Time'])
        minutes = self.parent.status[upgrade]['minutes']
        
        eta = conf + datetime.timedelta(minutes=minutes)
        remaining_duration = ceil((eta - datetime.datetime.now()).total_seconds() / 60)
        
        assert self.upgrade_widgets[upgrade]['status'].cget('state') == 'normal'
        self.upgrade_widgets[upgrade]['status'].delete(0, 'end')
        self.upgrade_widgets[upgrade]['status'].insert(0, from_minutes(remaining_duration))
        
        self.upgrade_widgets[upgrade]['eta'].config(text=eta.strftime("%Y-%m-%d %H:%M:%S"))
