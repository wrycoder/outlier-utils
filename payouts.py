#!/usr/bin/env python3

import sys, re, time, datetime, pytz
from datetime import timedelta
import pandas as pd
import numpy as np

USAGE = """USAGE: [python] payouts [csv] [yymmdd]?
    [csv]      path to comma-separated download of Outlier tasks
    [yymmdd]   (optional) date to examine

    If no date is specified, you will see tasks for the current day.
"""

class TimeCell:
    timeRE = re.compile('(([0-9]+)([hms]{1}))+')
    cell_contents = None
    def __init__(self, cell_contents):
        self.cell_contents = cell_contents

    def hours(self):
        for token in self.timeRE.findall(self.cell_contents):
            if token[2] == 'h':
                return int(token[1])
        return 0

    def minutes(self):
        for token in self.timeRE.findall(self.cell_contents):
            if token[2] == 'm':
                return int(token[1])
        return 0

    def seconds(self):
        for token in self.timeRE.findall(self.cell_contents):
            if token[2] == 's':
                return int(token[1])
        return 0

    def total_seconds(self):
        result = 0
        for token in self.timeRE.findall(self.cell_contents):
            match token[2]:
                case 'h':
                    result += int(token[1]) * 3600
                case 'm':
                    result += int(token[1]) * 60
                case 's':
                    result += int(token[1])
        return result

        if timeMatch[2] != None:
            hourMatch = self.hoursOnlyRE.match(self.cell_contents)
            try:
                result = int(hourMatch[1]) * 3600
            except: pass
        if timeMatch[4] == None:
            minuteMatch = self.minutesOnlyRE.match(self.cell_contents)
            try:
                result += int(minuteMatch[1]) * 60
            except: pass
        else:
            result += self.minutes() * 60
        return result + self.seconds()

class PayoutDate:
    target_date = None
    def __init__(self, target_date: str = None):
        if target_date is None:
            self.target_date = datetime.datetime.now(pytz.timezone('US/Eastern'))
        else:
            self.target_date = datetime.datetime.strptime(
                                target_date, '%y%m%d'
                               ).astimezone(pytz.timezone(
                                'US/Eastern'))

    def mdy(self):
        return self.target_date.strftime('%b %-d, %Y')

    def includes(self, date_string):
        comparison_date = datetime.datetime.strptime(
                                date_string, '%b %d, %Y'
                            ).astimezone(pytz.timezone(
                                'US/Eastern'))
        # A valid record may have the next calendar day,
        # because the source database is set to UTC and I
        # sometimes work pretty late in the evening in my timezone
        # (US/Eastern).
        utc_offset = timedelta(days=1)
        if (comparison_date.date() == self.target_date.date()):
            return True
        else:
            utc_date = self.target_date + utc_offset
            if(comparison_date.date() == utc_date.date()):
                return True
        return False

def to_hhmmss(raw_seconds: int):
    whole_hours = str(raw_seconds // 3600) + ':' if (raw_seconds > 3600) else ''
    leftover_minutes = raw_seconds % 3600
    minutes_integer = leftover_minutes // 60
    if minutes_integer == 0:
        whole_minutes = '00:'
    else:
        whole_minutes = f"{minutes_integer:02}:" if (leftover_minutes > 60) else ':'
    return whole_hours + whole_minutes + f"{(leftover_minutes % 60):02}"

def payouts_main(args: list = []):
    paydate = None
    if len(args) < 1:
        raise(Exception('ERROR: Too few arguments'))

    if len(args) == 2:
        paydate = PayoutDate(target_date=args[1])
    elif len(args) == 1:
        paydate = PayoutDate()
    else:
        raise(Exception(f"ERROR: Incorrect number of arguments ({len(args)})"))

    payouts = pd.read_csv(args[0])
    mission_tasks = []
    task_ids = []
    money_earned = 0
    dollarRE = re.compile(r"\$([0-9]+)\.([0-9]+)")
    index = 0
    while index < len(payouts):
        if paydate.includes(payouts.iloc[index]['workDate']):
            if payouts.iloc[index]['payType'] != 'missionReward':
                mission_tasks.append(payouts.iloc[index])
                if payouts.iloc[index]['itemID'] not in task_ids:
                    task_ids.append(payouts.iloc[index]['itemID'])
            else:
                payMatch = dollarRE.match(payouts.iloc[index]['payout'])
                if payMatch is not None:
                    money_earned += int(payMatch[1] + payMatch[2])
        index += 1
    work_time = 0
    for record in mission_tasks:
        if(record['duration'] != '-') and type(record['duration']) == str:
            task = TimeCell(record['duration'].rstrip())
            work_time += task.total_seconds()
        payMatch = dollarRE.match(record['payout'])
        if payMatch is not None:
            money_earned += int(payMatch[1] + payMatch[2])
    return(f"Total tasks found: {len(payouts)}\n"
           + f"Mission tasks found: {len(task_ids)}\n"
           + f"Total time worked: {to_hhmmss(work_time)}\n"
           + f"Total earnings: ${(money_earned/100):.2f}")

if __name__ == '__main__':
    try:
        result = payouts_main(sys.argv[1:])
        print(result)
    except Exception as ex:
        print(ex)
        print(f"\n{USAGE}")

