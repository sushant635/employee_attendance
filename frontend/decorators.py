from django.http import HttpResponse
from django.shortcuts import redirect
# import datetime
from datetime import datetime,timedelta

def unauthenticated_user(view_func):
    def wrapper_func(request,*args,**kwargs):
        if request.user.is_authenticated:
            return redirect('wallpost')

        else:
            return view_func(request,*args,**kwargs)

    return wrapper_func


def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request,*args,**kwargs):
            
            group = None
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name

            if group in allowed_roles:
                return view_func(request, *args,**kwargs)

            else:
                return HttpResponse("You are not authorized to view this page")

        return wrapper_func
    
    return decorator


def employee_only(view_func):
    def wrapper_func(request,*args,**kwargs):
        group = None
        if request.user.groups.exists():
            group = request.user.groups.all()[0].name
        if group == 'admin' or group == 'team_leader' :
            print('working')
            return redirect('team_attendance')

        if group == 'employee':
            print('working')
            return view_func(request,*args,**kwargs)
    return wrapper_func






def last_day_of_month(any_day):
    # this will never fail
    # get close to the end of the month for any day, and add 4 days 'over'
    next_month = any_day.replace(day=28) + timedelta(days=4)
    # subtract the number of remaining 'overage' days to get last day of current month, or said programattically said, the previous day of the first of next month
    return next_month - timedelta(days=next_month.day)




def attending_status(shift_in_time,shift_out_time,shift_out_var,shift_in_time_split,shift_out_time_split,in_time,out_time,in_time_split,out_time_split,worked_hours,attendance_date):
    employee_status = ''
    if shift_in_time_split:
        cutoff_in_time=float(shift_in_time_split)+1.00
        cutoff_half_day=float(cutoff_in_time)+1.00
    if shift_out_time_split:
        cutoff_out_time=float(shift_out_time_split)
    if shift_out_var == 'pm':
        if cutoff_out_time == 1.0:
            cutoff_out_time=13.0
        elif cutoff_out_time == 2.0:
            cutoff_out_time=14.0
        elif cutoff_out_time == 3.0:
            cutoff_out_time=15.0
        elif cutoff_out_time == 4.0:
            cutoff_out_time=16.0
        elif cutoff_out_time == 5.0:
            cutoff_out_time=17.0
        elif cutoff_out_time == 6.0:
            cutoff_out_time=18.0
        elif cutoff_out_time == 7.0:
            cutoff_out_time=19.0
        elif cutoff_out_time == 8.0:
            cutoff_out_time=20.0
        elif cutoff_out_time == 9.0:
            cutoff_out_time=21.0
        elif cutoff_out_time == 10.0:
            cutoff_out_time=22.0
        elif cutoff_out_time == 11.0:
            cutoff_out_time=23.0
    in_time_float=0.0
    out_time_float=0.0
    if in_time_split:
        in_time_float=float(in_time_split)
    if out_time_split:
        out_time_float=float(out_time_split)
    if in_time_float > cutoff_half_day:
        half_day_flag=True
    else:
        half_day_flag=False
    if in_time_float and cutoff_in_time:
        if in_time_float > cutoff_in_time:
            diff_in_time=in_time_float - cutoff_in_time
            diff_in_time_val=str(diff_in_time).split('.')
            diff_in_time_replace=str(
							'%.2f' % diff_in_time).replace('.', ':')
    if out_time_float and cutoff_out_time:
        if out_time_float < cutoff_out_time:
            diff_out_time=cutoff_out_time - out_time_float
            diff_out_time_val=str(diff_out_time).split('.')
            diff_out_time_val_one=diff_out_time_val[1]
            if int(diff_out_time_val_one) > 60:
                diff_out_time=diff_out_time - 0.40
                diff_out_time_replace=str('%.2f' % diff_out_time).replace('.', ':')
    day=datetime.strptime(
					attendance_date, '%Y-%m-%d').strftime('%A')
    if day in ('Saturday', 'Sunday'):
        if worked_hours >= 3.3:
            employee_status = 'Present'
        if worked_hours < 3.3:
            employee_status='Absent'
    elif day not in ('Saturday', 'Sunday'):
        if worked_hours >= 7.0:
            employee_status = 'Present'
        elif worked_hours >= 4 and worked_hours <= 7.0:
            employee_status = "Half Day"
        else:
            employee_status = 'Absent'
    return employee_status


def todays_status(worked_hours,attendance_date):
    employee_status = ''
    day=datetime.strptime(
					attendance_date, '%Y-%m-%d').strftime('%A')

    if day in ('Saturday', 'Sunday'):
        if worked_hours >= 3.3:
            employee_status = 'Present'
        if worked_hours < 3.3:
            employee_status='Absent'
    elif day not in ('Saturday', 'Sunday'):
        if worked_hours >= 7.0:
            employee_status = 'Present'
        elif worked_hours >= 4 and worked_hours <= 7.0:
            employee_status = "Half Day"
        else:
            employee_status = 'Absent'
    return employee_status