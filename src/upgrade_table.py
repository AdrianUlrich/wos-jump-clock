import datetime
import tkinter as tk
from math import ceil

from src.data.constants import *
from src.data.dependencies import depends_on
from src.time_conversions import from_minutes, to_minutes
from src.unit_conversions import to_units

EXPLANATION = """
        This table shows the cost of upgrading buildings to the next level. The cost is in terms of Meat, Wood, Coal, Iron, and Crystal, modified by Zinman's skill.
        Duration is the result of the formula: base_duration * (1/(1+construction_speed)) * (1-bonus_1) * ...
        Status will be modifiable if the upgrade is available. To start an upgrade, simply enter the current indicated ETA (XdYhZm) in the field.
        GREEN: Done, RED: Locked, WHITE: Available, BLUE: In Progress
        """

HEADERS = [COLUMN_BUILDING, COLUMN_LEVEL, COLUMN_MEAT, COLUMN_WOOD, COLUMN_COAL, COLUMN_IRON, COLUMN_CRYSTAL,
           COLUMN_RFC, 'Base Duration', COLUMN_DURATION, 'Status', 'Confirm Status', 'ETA']


class UpgradeTable(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.cost_data = parent.cost_data
        self.seconds = None
        
        # WIDGETS
        self.explanation = tk.Label(self, text=EXPLANATION, justify='left')
        self.headers = {header: tk.Label(self, text=header, borderwidth=1, relief="solid") for header in HEADERS}
        self.upgrade_widgets = {}
        self.refresh_button = tk.Button(self, text='↻', command=self.update_table)
        self.countdown_label = tk.Label(self, text='Countdown')
        
        # LAYOUT
        self.explanation.grid(row=0, column=0, columnspan=len(HEADERS), sticky=tk.NW)
        self.countdown_label.grid(row=0, column=len(HEADERS), sticky=tk.SE)
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
        
        totals = [0] * 7  # meat, wood, coal, iron, crystal, rfc, duration
        for i, upgrade in enumerate(ordered_todo):
            # we can assume the widget is either already in the right place, or not there at all
            building, level = upgrade
            if upgrade in status and upgrade in self.upgrade_widgets:
                # just update the status
                self.update_status(upgrade)
                continue
            
            row = self.cost_data[(self.cost_data['Building'] == building) & (self.cost_data['Level'] == level)]
            meat = row[COLUMN_MEAT].values[0]
            wood = row[COLUMN_WOOD].values[0]
            coal = row[COLUMN_COAL].values[0]
            iron = row[COLUMN_IRON].values[0]
            crystal = row[COLUMN_CRYSTAL].values[0]
            rfc = row[COLUMN_RFC].values[0]
            base_duration = row[COLUMN_DURATION].values[0]
            minutes = row[COLUMN_MINUTES].values[0]
            
            # rss cost reduction
            meat = ceil(to_units(meat) * self.parent.zinman_skill)
            wood = ceil(to_units(wood) * self.parent.zinman_skill)
            coal = ceil(to_units(coal) * self.parent.zinman_skill)
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
                'coal_label': tk.Label(self, text=coal),
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
            widgets['coal_label'].grid(row=i + 2, column=5)
            widgets['iron_label'].grid(row=i + 2, column=6)
            widgets['crystal_label'].grid(row=i + 2, column=7)
            widgets['rfc_label'].grid(row=i + 2, column=8)
            widgets['base_duration_label'].grid(row=i + 2, column=9)
            widgets['duration_label'].grid(row=i + 2, column=10)
            widgets['status'].grid(row=i + 2, column=11)
            widgets['confirm_status'].grid(row=i + 2, column=12)
            widgets['eta'].grid(row=i + 2, column=13)
            
            # tally the totals
            totals[0] += meat
            totals[1] += wood
            totals[2] += coal
            totals[3] += iron
            totals[4] += crystal
            totals[5] += rfc
            if upgrade not in status:
                totals[6] += discounted_minutes
            else:
                eta = datetime.datetime.fromtimestamp(status[upgrade]['Confirmed Time']) + datetime.timedelta(
                    minutes=status[upgrade]['minutes'])
                remaining_duration = ceil((eta - datetime.datetime.now()).total_seconds() / 60)
                totals[6] += remaining_duration
        
        # update the totals
        self.update_totals(totals)
    
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
        if upgrade not in self.upgrade_widgets:
            return
        
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
    
    def update_totals(self, totals):
        meat, wood, coal, iron, crystal, rfc, duration = totals
        
        # meat and wood are worth 1, coal is worth 5 and iron is worth 20
        rss = meat + wood + coal * 5 + iron * 20
        
        parent_resources_dict = self.parent.resources_dict
        missing_meat = max(0, meat - parent_resources_dict['Meat'])
        missing_wood = max(0, wood - parent_resources_dict['Wood'])
        missing_coal = max(0, coal - parent_resources_dict['Coal'])
        missing_iron = max(0, iron - parent_resources_dict['Iron'])
        missing_crystal = max(0, crystal - parent_resources_dict['Crystal'])
        missing_rfc = max(0, rfc - parent_resources_dict['RFC'])
        missing_speedups = max(0, duration - parent_resources_dict['Speedups'])
        
        missing_rss = missing_meat + missing_wood + missing_coal * 5 + missing_iron * 20 + missing_crystal
        
        # update the totals (for now in the explanation label)
        self.explanation.config(text=f'{EXPLANATION}'
                                     f'Total RSS: {rss:,}, Total Duration: {from_minutes(duration)}'
                                     f'Missing RSS: {missing_rss:,}, Missing Speedups: {from_minutes(missing_speedups)}')
        
        # update the countdown
        if self.seconds is None:
            self.seconds = ceil(missing_speedups * 60)
            self.update_countdown()

    def update_countdown(self):
        if self.seconds is None:
            return
        
        self.seconds -= 1
        minutes, seconds = divmod(self.seconds, 60)
        self.countdown_label.config(text=f'{from_minutes(minutes)} {seconds:02d}')
        if self.seconds == 0:
            self.update_table()
            self.seconds = None
        self.after(1000, self.update_countdown)