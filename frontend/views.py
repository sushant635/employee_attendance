from django.shortcuts import render,redirect
from frontend.forms import UserForm,UserProfileInfoForm ,PostForm
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
import sys
from django.contrib.auth.models import Group
from django.urls import reverse
import  xmlrpc.client
import datetime
from datetime import datetime, timedelta, date
import PIL.Image as Image
import io
import base64
from frontend.models import User,RegisterModel
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.utils.html import format_html
from .decorators import unauthenticated_user,allowed_users,employee_only,last_day_of_month ,attending_status,todays_status
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
import pandas as pd 
import requests
import os
import json
import pytz
from dateutil import tz
from django.contrib import messages
import logging




# Create your views here.
url = 'http://localhost:8069/'
db = 'quikhr_safr_staging_12_07_2021'
username = 'admin'
password = 'qhradmin@123'


common = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/common')
output = common.version()
print('details..',output)
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/object')

def listToString(s): 
    str1 = "" 
    for ele in s: 
        str1 += ele    
    return str1 

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))

@unauthenticated_user
def register(request):
    try:
        registered = False
        if request.method == 'POST':
            user_form = UserForm(data=request.POST)
            profile_form = UserProfileInfoForm(data=request.POST)
            if user_form.is_valid() and profile_form.is_valid():
                user = user_form.save()

                group = Group.objects.get(name='employee')

                user.groups.add(group)

                user.set_password(user.password)


                user.save()
                profile = profile_form.save(commit=False)
                profile.user = user 
                if 'employee_code' in request.POST:
                    profile.employee_code = request.POST.get('employee_code')
                profile.save()
                registered = True
            else:
                print(user_form.errors,profile_form.errors)
            return HttpResponseRedirect(reverse('login'))
        else:
            user_form = UserForm()
            profile_form = UserProfileInfoForm()
        return render(request,'register.html',{'user_form':user_form,'profile_form':profile_form,'registered':registered})
    except Exception as e:
        print(e,'line number {}'.format(sys.exc_info()[-1].tb_lineno))


@unauthenticated_user
def user_login(request):
    try:
        if request.method == "POST":
            print(request.POST)
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(username=username,password=password)
            if user:
                if user.is_active:
                    login(request, user)
                    print(request.POST.get('chek'))
                    if request.POST.get('chek'):
                        print('working')
                        response = HttpResponseRedirect(reverse('wallpost'))
                        # response = HttpResponse('working')
                        response.set_cookie('username',request.POST.get('username'),max_age=1209600)
                        response.set_cookie('password',request.POST.get('password'),max_age=1209600)
                        print(response)
                        return response
                    return redirect('wallpost')
                else:
                    return HttpResponse('You account was inactive')
            else:
                print("someone tried to login and failed")
                print("They used username:{} and {}".format(username,password))
                return HttpResponse("Invalid login details given")
        else:
            if request.COOKIES.get('username'):
                print('working')
                print(request.COOKIES['username'])
                return render(request, 'login.html', {'username':request.COOKIES['username'],'password':request.COOKIES['password']})
            else:
                print('not working')
                return render(request,'login.html')

    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)


try: 
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup
@login_required
def wallpost(request):
    try:
        current_user = request.user
        user_id = current_user.id
        user = User.objects.get(id=user_id)
        emp_code = RegisterModel.objects.get(user=user).employee_code
        ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',emp_code,]]],)

        detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [ids],{'fields': ['name','image']})
        child_list = []
        emp_name = {}
        for i in detail:
            emp_name = {'name':i['name'],'image':i['image']}


        wall_ids = models.execute_kw(db, uid, password,
        'wall.post.points', 'search',
        [[]],)
        wallpost_detail = models.execute_kw(db, uid, password,
        'wall.post.points', 'read',
        [wall_ids],{'fields': ['name','display_name','create_date','write_date','create_uid']})
        wall_list = []
        for i in wallpost_detail:
            html = i['name']
            print(html)
            parsed_html = BeautifulSoup(html)
            # print(parsed_html.find('img').text)
            print(parsed_html)
            # print(i[])
            create_uid1 = i['create_uid']
            create_uid = create_uid1[1]
            name = i['name']
            # print(format_html(name))
            create_date1 = i['create_date']
            create_date2 = datetime.strptime(str(create_date1), "%Y-%m-%d %H:%M:%S").date()
            create_date = create_date2.strftime("%d-%m-%Y")            
            wall_list.append({'create_name':create_uid,'name':format_html(name),'create_date':create_date})
            
          
        context = {'wall':wall_list,'emp_name':emp_name}
        # return HttpResponse('working')
        return render(request,'index.html',context)
 
    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))

# @allowed_users(allowed_roles=['admin'])
@login_required
def employee_profile(request):
    try:
        current_user = request.user
        user_id = current_user.id
        user = User.objects.get(id=user_id)
        emp_code = RegisterModel.objects.get(user=user).employee_code
        print(emp_code)
        ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',emp_code,]]],)

        detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [ids],{'fields': ['child_ids','name','image']})
        emp_name = {}
        for i in detail:
            emp_name = {'name':i['name'],'image':i['image']}

        emp_ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[]],)
        # print(emp_ids)
        emp_detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [emp_ids],{'fields': ['name','department_id','category_ids','job_id','parent_id','emp_code','image']})
        # print(emp_detail)
        today1 = date.today()
        today = today1.strftime("%Y-%m-%d")
        first = today1.replace(day=1)
        first1 = first.strftime("%Y-%m-%d")
        present = 0
        child = []
        for i in emp_detail:
            child_emp_code = i['emp_code']
            count_ids = models.execute_kw(db, uid, password,
            'hr.attendance', 'search',
            [[['employee_code','=',child_emp_code,],['attendance_date','<=',today],['attendance_date','>=',first1]]],)
            
            count = models.execute_kw(db, uid, password,
            'hr.attendance', 'read',
            [count_ids],{'fields': ['attendance_date','worked_hours','shift','employee_status']})
            for counts in count:
                status = counts['employee_status']

                if status == 'P':
                    present += 1

            # print
            dict1 = {'name':i['name'],'emp_code':i['emp_code'],'present':present}
            job = i['job_id']
            if job != False:
                dict1['job'] = job[1]
            else:
                dict1['job'] = job
            parent = i['parent_id']
            if parent != False:
                dict1['parent'] = parent[1]
            else:
                dict1['parent'] = parent
            image1 = i['image']
            if image1 != False:
                # print(image1)
                b = base64.b64decode(image1)
                image =  base64.b64encode(b).decode("utf-8")
                dict1['image'] = image
            else:
                # img = Image.open('http://localhost:8000/static/img/user_admin.png')
                # im = Image.open(requests.get('http://localhost:8000/static/img/user_admin.png', stream=True).raw)
                # print(im)
                # with open(im, "rb") as image_file:
                    # encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                    # print(encoded_string)
                dict1['image'] = image1
            child.append(dict1)
                
       
        demp_ids = models.execute_kw(db, uid, password,
        'hr.department', 'search',
        [[]],)

        demp_detail = models.execute_kw(db, uid, password,
        'hr.department', 'read',
        [demp_ids],{'fields': ['name']})  
         
        site_ids = models.execute_kw(db, uid, password,
        'site.master', 'search',
        [[]],)   
        site_detail = models.execute_kw(db, uid, password,
        'site.master', 'read',
        [site_ids],{'fields': ['name']}) 

        context = {'emp_list':child,'emp_name':emp_name,'demp':demp_detail,'site':site_detail}
        # print(context)

        return render(request,'employee_profile.html',context)
    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))


@login_required
def employee_details(request,emp_code):
    try:
        current_user = request.user
        user_id = current_user.id
        user = User.objects.get(id=user_id)
        Login_emp_code = RegisterModel.objects.get(user=user).employee_code
        print('employee code',emp_code)
        ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',Login_emp_code,]]],)

        detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [ids],{'fields': ['child_ids','name','image']})
        child_list = []
        emp_name = {}
        for i in detail:
            emp_name = {'name':i['name'],'image':i['image']}
        print('employee code',emp_code)
        emp_ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',emp_code]]],)
        emp_detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [emp_ids],{'fields': ['personal_email','personal_mobile','name','department_id','category_ids','grade_id',
        'job_id','message_needaction','inactive','parent_id','coach_id','department_id','company_id',
        'emp_code','image','position_type','joining_date','confirmation_date','esic_location','site_master_id',
        'notice_period','father_name','address','mother_name','same_as_current','spouse_name','gender',
        'marital','emergency_contact_name','birthday','emergency_contact_number','physically_disabled',
        'blood_group','country_id','bank_id','state_id','bank_account_number','pan','branch_name','aadhar','ifsc_code',
        'passport_id','passport_expire_date','visa_no','visa_expire','per_address','emergency_contact_relation','site_location_id','work_email','work_phone','cost_center_id',
        'emp_category','mobile_phone','shift_id','experiance_id','highest_qualification','weekly_off','appraisal_cycle','previous_company','previous_designation','pf_uan_no','esic_uan_no',
        'user_id','address_id','address_home_id','barcode','employee_billing_status','po_received','person_id']})
        
        holiday_ids =  models.execute_kw(db, uid, password,'holiday.master', 'search',[[]],)
        holidays  = models.execute_kw(db, uid, password,'holiday.master', 'read',[holiday_ids],{'fields': ['name','holiday_date','active']})
        holiday_list = []
        for i in holidays:
            holiday = {'holiday_name':i['name'],'holiday_date':i['holiday_date']}
            holiday['days'] = datetime.strptime(i['holiday_date'], '%Y-%m-%d').strftime('%A')
            active = ''
            if i['active'] == True:
                active = 'checked'
            else:
                active = ''
            holiday['active'] = active

            holiday_list.append(holiday)



        for i in emp_detail:
            # print(i['same_as_current'])
            profile_details = {'emp_code':i['emp_code'],'name':i['name'],'grade':i['grade_id'][1],'dempartment':i['department_id'][1],'designation':i['job_id'][1],
            'reporting':i['parent_id'][1],'joining_date':i['joining_date'],'confirmation_date':i['confirmation_date'],'status':i['position_type'],'notice':i['notice_period']}
            image1 = i['image']
            if image1 != False:
                b = base64.b64decode(image1)
                image =  base64.b64encode(b).decode("utf-8")
                profile_details['image'] = image
            else:
                profile_details['image'] = image1
            spouse_name = i['spouse_name']
            if spouse_name == False:
                spouse_name = ''
            emergency_contact_name = i['emergency_contact_name']
            if emergency_contact_name == False:
                emergency_contact_name = ''
            emergency_contact_relation = i['emergency_contact_relation']
            if emergency_contact_relation == False:
                emergency_contact_relation = ''

            bank_id = i['bank_id']
            if bank_id == False:
                bank_id = ''
            else:
                bank_id = bank_id[1]
            branch_name = i['branch_name']
            if branch_name == False:
                branch_name = ''
            ifsc_code = i['ifsc_code']
            if ifsc_code == False:
                ifsc_code = ''
            passport_id = i['passport_id']
            if passport_id == False:
                passport_id = ''
            passport_expire_date = i['passport_expire_date']
            if passport_expire_date == False:
                passport_expire_date = ''
            visa_no = i['visa_no']
            if visa_no == False:
                visa_no = ''
            visa_expire = i['visa_expire']
            if visa_expire == False:
                visa_expire = ''

            work_phone = i['work_phone']
            if work_phone == False:
                work_phone = ''
            weekly_off = i['weekly_off']
            if weekly_off == False:
                weekly_off = ''
            appraisal_cycle = i['appraisal_cycle']
            if appraisal_cycle == False:
                appraisal_cycle = ''
            previous_company = i['previous_company']
            if previous_company == False:
                previous_company = ''
            previous_designation = i ['previous_designation']
            if previous_designation == False:
                previous_designation = ''
            user_id = i['user_id']
            if user_id == False:
                user_id = ''
            address_id = i['address_id']
            if address_id == False:
                address_id = ''
            
            # profile_detail.append(profile_details)
            blood = i['blood_group']
            if blood =='a_negative':
                blood_group = 'A-ve'
            elif blood == 'a_positive':
                blood_group = 'A+ve'
            elif blood == 'b_positive':
                blood_group = 'B+ve' 
            elif blood == 'b_negative':
                blood_group = 'B-ve' 
            elif blood == 'ab_positive':
                blood_group = 'AB+ve' 
            elif blood == 'ab_negative':
                blood_group = 'AB-ve' 
            elif blood == 'o_positive':
                blood_group = 'O+ve'
            elif blood == 'o_negative':
                blood_group = 'O-ve'
            else:
                blood_group = 'NA'
            
            same_as_current = i['same_as_current']
            # print(same_as_current)
            if same_as_current == True:
                same = 'checked'
            else:
                same = ''
            # print(same)
            print(i['site_location_id'])
            emp = {'father_name':i['father_name'],'mother_name':i['mother_name'],'spouse_name':spouse_name,'birthday':i['birthday'],'blood_group':blood_group,
            'physicall_disabled':i['physically_disabled'],'gender':i['gender'],'marital':i['marital'],'address':i['address'],'same':same,'per_address':i['per_address'],
            'personal_email':i['personal_email'],'personal_mobile':i['personal_mobile'],'emergency_contact_name':emergency_contact_name,'emergency_contact_number':i['emergency_contact_number'],
            'emergency_contact_relation':emergency_contact_relation,'country_id':i['country_id'][1],'state_id':i['state_id'][1],'pan':i['pan'],'aadhar':i['aadhar'],'bank_id':bank_id,
            'bank_account_number':i['bank_account_number'],'branch_name':branch_name,'ifsc_code':ifsc_code,'passport_id':passport_id,'passport_expire_date':passport_expire_date,
            'visa_no':visa_no,'visa_expire':visa_expire,'company_id':i['company_id'][1],'site_master_id':i['site_master_id'][1],'work_email':i['work_email'],'work_phone':work_phone,
            'cost_center_id':i['cost_center_id'][1],'emp_category':i['emp_category'],'mobile_phone':i['mobile_phone'],'shift_id':i['shift_id'][1],'experiance_id':i['experiance_id'][1],
            'highest_qualification':i['highest_qualification'],'weekly_off':weekly_off,'appraisal_cycle':appraisal_cycle,'previous_company':previous_company,'previous_designation':previous_designation,
            'position_type':i['position_type'],'esic_uan_no':i['esic_uan_no'],'user_id':user_id,'address_id':address_id,'address_home_id':i['address_home_id'],'barcode':i['barcode'],
            'employee_billing_status':i['employee_billing_status'],'po_received':i['po_received'],'person_id':i['person_id']} 

            # emp_details.append(emp)

        context = {'profile_details':profile_details,'emp':emp,'emp_name':emp_name,'holidays':holiday_list}

        # print(context)
        return render(request,'employee_details.html',context)

    except Exception as e:
        print(e,'line number {}'.format(sys.exc_info()[-1].tb_lineno))


@login_required
@employee_only
def attendance_base(request):
    try:
        
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Asia/Kolkata')
        current_user = request.user
        user_id = current_user.id
        user = User.objects.get(id=user_id)
        emp_code = RegisterModel.objects.get(user=user).employee_code
        print(emp_code)
        ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',emp_code,]]],)

        detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [ids],{'fields': ['name','image']})
        child_list = []
        emp_name = {}
        for i in detail:
            emp_name = {'name':i['name'],'image':i['image']}
        # cron job for import safr attendaces data #############################
        # models.execute_kw(db, uid, password,
        # 'ir.cron', 'method_direct_trigger',[[]],)

        # models.execute_kw(db,uid,password,
        # 'safr.attendance.records','cron_safr_import_attendance_master',[[]])
        #############################################end cron ###############
        #for today attendaces
        today = date.today()
        today = today.strftime("%Y-%m-%d")
        todays_ids = models.execute_kw(db, uid, password,
        'hr.attendance', 'search',
        [[['employee_code','=',emp_code],['attendance_date','=',today]]],)
        days = date.today().strftime('%A')
        today_details = emp_detail = models.execute_kw(db, uid, password,
        'hr.attendance', 'read',
        [todays_ids],{'fields': ['employee_code','employee_name','attendance_date','in_time','out_time','worked_hours','employee_status','import_status','source_id_in','source_id_out','employee_status']})
        today_atte_data = {}
        for i in today_details:
            status = i['employee_status']
            if status == 'AB':
                status = 'Absent'
            elif status == 'P':
                status = 'Present'
            elif status == 'half_day_p_ab':
                status = 'Half Day'
            today_atte_data = {'employee_code':i['employee_code'],'attendance_date':i['attendance_date'],'import_status':i['import_status'],'check_in':i['in_time'],'check_out':i['out_time'],
            'source_id_in':i['source_id_in'],'source_id_out':i['source_id_out'],'status':status,'worked_hours':i['worked_hours']}
            
        image_ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',emp_code,]]],)
        
        image_detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [image_ids],{'fields': ['image','emp_code','name','shift_id']})
        img_list = []
        shift = []
        for i in image_detail:
            emp_dict = {'name':i['name'],'emp_code':i['emp_code']}
            shift_id = i['shift_id']
            # print(shift_id)
            shift.append(shift_id)
            image1 = i['image']
            if image1 != False:
                b = base64.b64decode(image1)
                # print(img)
                # img = Image.open(io.BytesIO(b))
                image =  base64.b64encode(b).decode("utf-8")
                # img.show()
                # img_list.append(image)
                emp_dict['image'] = image
            else:
                # img_list.append(image1)
                emp_dict['image'] = image1
            img_list.append(emp_dict)
        holidays_ids = models.execute_kw(db, uid, password,
        'hr.holidays', 'search',
        [[['employee_code','=',emp_code,]]],)

        holidays_detail = models.execute_kw(db, uid, password,
        'hr.holidays', 'read',
        [holidays_ids],{'fields': ['total_days','holiday_status_id','date_from_new','date_to_new']})
        print(holidays_detail)


        emp_ids = models.execute_kw(db, uid, password,
        'hr.attendance', 'search',
        [[['employee_code','=',emp_code,]]],)

        atten_detail = models.execute_kw(db, uid, password,
        'hr.attendance', 'read',
        [emp_ids],{'fields': ['attendance_date','in_time','out_time','worked_hours','shift','employee_status']})

        present = 0
        absent = 0
        half_day = 0 
        today1 = date.today()
        print(present,absent)
        first = today1.replace(day=1)
        first1 = first.strftime("%Y-%m-%d")
        count_ids = models.execute_kw(db, uid, password,
        'hr.attendance', 'search',
        [[['employee_code','=',emp_code,],['attendance_date','<=',today],['attendance_date','>=',first1]]],)
        
        count = models.execute_kw(db, uid, password,
        'hr.attendance', 'read',
        [count_ids],{'fields': ['attendance_date','in_time','out_time','worked_hours','shift','employee_status']})
        for i in count:
            status = i['employee_status']
            if status == 'AB':
                absent += 1
            elif status == 'P':
                present += 1
            elif status == 'half_day_p_ab':
                half_day += 1
        attend_list = []
        for i in atten_detail:
            status = i['employee_status']
            if status == 'AB':
                status = 'Absent'
            elif status == 'P':
                status = 'Present'
            elif status == 'half_day_p_ab':
                status = 'Half Day'
            emp_dict = {'attendance_date':i['attendance_date'],'check_in':i['in_time'],'check_out':i['out_time'],'status':status,'worked_hours':i['worked_hours']}
            attend_list.append(emp_dict)

        last = last_day_of_month(today1)
        print(last)
        print(today_atte,days)
        context = {'image':img_list,'emp':emp_detail,'today_atte':today_atte_data,'days':days,'firstday':first,'lastday':last,'attendance':attend_list,
        'present':present,'absent':absent,'half_day':half_day,'emp_name':emp_name}
        # print(context)
        return render(request,'main_attendance.html',context)

    except Exception as e:
        print(e,'line number {}'.format(sys.exc_info()[-1].tb_lineno))




def team_attendance(request):
    try:
        today = date.today()
        today = today.strftime("%Y-%m-%d")
        current_user = request.user
        user_id = current_user.id
        user = User.objects.get(id=user_id)
        emp_code = RegisterModel.objects.get(user=user).employee_code
        print(emp_code)
        ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',emp_code,]]],)

        detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [ids],{'fields': ['name','image']})
        child_list = []
        emp_name = {}
        for i in detail:
            emp_name = {'name':i['name'],'image':i['image']}
        image_ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',emp_code,]]],)

        image_detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [image_ids],{'fields': ['emp_code','name','shift_id','child_ids']})

        demp_ids = models.execute_kw(db, uid, password,
        'hr.department', 'search',
        [[]],)

        demp_detail = models.execute_kw(db, uid, password,
        'hr.department', 'read',
        [demp_ids],{'fields': ['name']})
        ##################################################child details ################################
        child_list = []
        childs_ids_list = []
        for i in image_detail:
            id = i['child_ids']
            child_ids = models.execute_kw(db, uid, password,
            'hr.employee', 'search',
            [[['id','=',id,]]],)

            child_detail = models.execute_kw(db, uid, password,
            'hr.employee', 'read',
            [child_ids],{'fields': ['emp_code','name','shift_id','department_id']})

            child_list.append(child_detail)

        child_name = []
        for i in child_list:
            for j in i:
                # print(j['name'])
                emp1 = {'name':j['name'],'emp_code':j['emp_code']}
                child_name.append(emp1)
                temp = j['emp_code']
                childs_ids_list.append(temp)
                # print(temp)
        # print(childs_ids_list[0])
        child_emp_code = childs_ids_list[0]
        print(child_emp_code)
        print(child_name)
        child_image_ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',child_emp_code]]],)
        
        child_image_detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [child_image_ids],{'fields': ['image','emp_code','name','shift_id']})

        child_todays_ids = models.execute_kw(db, uid, password,
        'hr.attendance', 'search',
        [[['employee_code','=',child_emp_code],['attendance_date','=',today]]],)

        child_today_details = models.execute_kw(db, uid, password,
        'hr.attendance', 'read',
        [child_todays_ids],{'fields': ['employee_code','attendance_date','in_time','out_time','worked_hours','employee_status','import_status','source_id_in','source_id_out']})

        child_today_atte = []
        child_today_data = {}
        for i in child_today_details:
            status = i['employee_status']
            if status == 'AB':
                status = 'Absent'
            elif status == 'P':
                status = 'Present'
            elif status == 'half_day_p_ab':
                status = 'Half Day'
            child_today_data = {'employee_code':i['employee_code'],'attendance_date':i['attendance_date'],'import_status':i['import_status'],'check_in':i['in_time'],'check_out':i['out_time'],
            'source_id_in':i['source_id_in'],'source_id_out':i['source_id_out'],'status':status,'worked_hours':i['worked_hours']}
           
        child_img_list = []
        shift = []
        for i in child_image_detail:
            emp_dict = {'name':i['name'],'emp_code':i['emp_code']}
            shift_id = i['shift_id']
            # print(shift_id)
            shift.append(shift_id)
            image1 = i['image']
            if image1 != False:
                b = base64.b64decode(image1)
                # print(img)
                # img = Image.open(io.BytesIO(b))
                image =  base64.b64encode(b).decode("utf-8")
                # img.show()
                # img_list.append(image)
                emp_dict['image'] = image
            else:
                # img_list.append(image1)
                emp_dict['image'] = image1
            child_img_list.append(emp_dict)
        child_emp_ids = models.execute_kw(db, uid, password,
        'hr.attendance', 'search',
        [[['employee_code','=',child_emp_code,]]],)

        child_atten_detail = models.execute_kw(db, uid, password,
        'hr.attendance', 'read',
        [child_emp_ids],{'fields': ['attendance_date','in_time','out_time','worked_hours','shift','employee_status',]})
        today1 = date.today()
        first = today1.replace(day=1)
        first1 = first.strftime("%Y-%m-%d")
       
        child_attend_list = []
        child_count_ids = models.execute_kw(db, uid, password,
        'hr.attendance', 'search',
        [[['employee_code','=',child_emp_code],['attendance_date','<=',today],['attendance_date','>=',first1]]],)
        child_count = models.execute_kw(db, uid, password,
        'hr.attendance', 'read',
        [child_count_ids],{'fields': ['attendance_date','in_time','out_time','worked_hours','shift','employee_status']})
        print(child_count)
        child_present = 0
        child_absent = 0
        child_half_day = 0 
        for i in child_count:
            print(i['employee_status'])
            status = i['employee_status']
            if status == 'AB':
                child_absent += 1
            elif status == 'P':
                child_present += 1
            elif status == 'half_day_p_ab':
                child_half_day += 1
        for i in child_atten_detail:
            status = i['employee_status']
            if status == 'AB':
                status = 'Absent'
            elif status == 'P':
                status = 'Present'
            elif status == 'half_day_p_ab':
                status = 'Half Day'
            emp_dict = {'attendance_date':i['attendance_date'],'check_in':i['in_time'],'check_out':i['out_time'],'status':status,'worked_hours':i['worked_hours']}
            child_attend_list.append(emp_dict)
        ##################################################################################################
        ####################################team leader #####################################
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Asia/Kolkata')
        todays_ids = models.execute_kw(db, uid, password,
        'hr.attendance', 'search',
        [[['employee_code','=',emp_code],['attendance_date','=',today]]],)
        print('todays ids',todays_ids)
        days = date.today().strftime('%A')
        today_details = emp_detail = models.execute_kw(db, uid, password,
        'hr.attendance', 'read',
        [todays_ids],{'fields': ['employee_code','attendance_date','in_time','out_time','worked_hours','employee_status','import_status','source_id_in','source_id_out']})
        today_atte = []
        today_atte_data = {}
        for i in today_details:
            status = i['employee_status']
            if status == 'AB':
                status = 'Absent'
            elif status == 'P':
                status = 'Present'
            elif status == 'half_day_p_ab':
                status = 'Half Day'
            today_atte_data = {'employee_code':i['employee_code'],'attendance_date':i['attendance_date'],'import_status':i['import_status'],'check_in':i['in_time'],'check_out':i['out_time'],
            'source_id_in':i['source_id_in'],'source_id_out':i['source_id_out'],'status':status,'worked_hours':i['worked_hours']}


    
        image_ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',emp_code,]]],)
        
        image_detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [image_ids],{'fields': ['image','emp_code','name','shift_id']})
        img_list = []
        shift = []
        for i in image_detail:
            emp_dict = {'name':i['name'],'emp_code':i['emp_code']}
            shift_id = i['shift_id']
            # print(shift_id)
            shift.append(shift_id)
            image1 = i['image']
            if image1 != False:
                b = base64.b64decode(image1)
                # print(img)
                # img = Image.open(io.BytesIO(b))
                image =  base64.b64encode(b).decode("utf-8")
                # img.show()
                # img_list.append(image)
                emp_dict['image'] = image
            else:
                # img_list.append(image1)
                emp_dict['image'] = image1
            img_list.append(emp_dict)

        ################################################
        holidays_ids = models.execute_kw(db, uid, password,
        'hr.holidays', 'search',
        [[['employee_code','=',emp_code,]]],)

        holidays_detail = models.execute_kw(db, uid, password,
        'hr.holidays', 'read',
        [holidays_ids],{'fields': ['total_days','holiday_status_id','date_from_new','date_to_new']})


        emp_ids = models.execute_kw(db, uid, password,
        'hr.attendance', 'search',
        [[['employee_code','=',emp_code,]]],)

        atten_detail = models.execute_kw(db, uid, password,
        'hr.attendance', 'read',
        [emp_ids],{'fields': ['attendance_date','in_time','out_time','worked_hours','shift','employee_status','site_master_id']})
        
        print('details',atten_detail)
        present = 0
        absent = 0
        half_day = 0 
        count_ids = models.execute_kw(db, uid, password,
        'hr.attendance', 'search',
        [[['employee_code','=',emp_code],['attendance_date','<=',today],['attendance_date','>=',first1]]],)
        count = models.execute_kw(db, uid, password,
        'hr.attendance', 'read',
        [count_ids],{'fields': ['attendance_date','in_time','out_time','worked_hours','shift','employee_status']})
        print('count',count)
        for i in count:
            status = i['employee_status']
            if status == 'AB':
                absent += 1
            elif status == 'P':
                present += 1
            elif status == 'half_day_p_ab':
                half_day += 1

        attend_list = []
        for i in atten_detail:
            status = i['employee_status']
            if status == 'AB':
                status = 'Absent'
            elif status == 'P':
                status = 'Present'
            elif status == 'half_day_p_ab':
                status = 'Half Day'
            emp_dict = {'attendance_date':i['attendance_date'],'check_in':i['in_time'],'check_out':i['out_time'],'status':status,'worked_hours':i['worked_hours']}
            attend_list.append(emp_dict)
    
        
        last = last_day_of_month(today1)
        context = {'image':img_list,'emp':emp_detail,'today_atte':today_atte_data,'days':days,'firstday':first,'lastday':last,'attendance':attend_list,
        'present':present,'absent':absent,'half_day':half_day,'childs':child_detail,'demp':demp_detail,'child_image':child_image_detail,
        'child_today':child_today_data,'child_attendance':child_attend_list,'child_present':child_present,'child_absent':child_absent,'child_half_day':child_half_day,
        'emp_name':emp_name,'child_name':child_name}

        #######################################################################################

        return render(request,'team_attendance.html',context)
    except Exception as e:
        print(e,'line number {}'.format(sys.exc_info()[-1].tb_lineno))


def create_wall_post(request):
    try:
        if request.method == "POST":
            post = request.POST.get('post')
            print(post)

            id = models.execute_kw(db, uid, password, 'wall.post.points', 'create', [{
           'name': post,
            }])
            
            return HttpResponseRedirect(reverse('create_wallpost'))

        else:
            myform = PostForm()
        
        return render(request,'create_wallpost.html',{'myform':myform})

    except Exception as e:
        print(e,'line number {}'.format(sys.exc_info()[-1].tb_lineno))



@csrf_exempt
def cron_create_attendance_csv(request):
    try:
        if request.method == "POST":
            print(request.POST)
            path = request.POST.get('path')
            since_date1 = request.POST.get('sincedate')
            print(since_date1,type(since_date1))
            since_date = datetime.strptime(since_date1, '%Y-%m-%d').strftime('%d/%m/%Y')
            print(since_date)
            ids = models.execute_kw(db, uid, password,
            'safr.credentials', 'search',[[]],)
            
            data = models.execute_kw(db, uid, password, 
            'safr.credentials', 'read',
            [ids],{'fields': ['account_id_safr', 'password_safr', 'non_safr_cloud_deploy','safr_dir','event_url','csv_dir']})
            
            safr_ids = models.execute_kw(db, uid, password,
            'hr.employee', 'search',[[]],)

            data2 = models.execute_kw(db, uid, password,
            'hr.employee', 'read',
            [safr_ids],{'fields': ['person_id','emp_code']})

            safr_dir = listToString([i['safr_dir'] for i in data ])
            safr_account_id = listToString([i['account_id_safr'] for i in data ])
            safr_password =  listToString([i['password_safr'] for i in data ])

            col_names = [
                    'date',
                    'EmpCode',
                    'InTime(HH:MM)',
                    'OutTime(HH:MM)',
                    'BiometricDate'
                ]

            df = pd.DataFrame(columns=col_names)
            # print(type(since_date),since_date)
            try:
                for each_person in data2:
                    if since_date:
                        since_timestamp = int(datetime.strptime(
                                since_date, '%d/%m/%Y').replace(tzinfo=tz.gettz('Asia/Kolkata')).timestamp() * 1000)
                    person_id = each_person['person_id']
                    if person_id:
                        headers = {
                                'accept': 'application/json;charset=UTF-8',
                                'X-RPC-DIRECTORY': safr_dir if safr_dir else 'main',
                                'X-RPC-AUTHORIZATION': str(safr_account_id)+':'+str(safr_password),
                            }
                        params = (('combineActiveEvents', 'false'),
                                ('personId', str(person_id)),   
                                ('rootEventsOnly', 'true'),
                                ('sinceTime', since_timestamp),
                                ('spanSources', 'false'),)

                        response=requests.get('https://cv-event.real.com/events', headers=headers, params=params)
                        # print(response)
                        # print(response.text)
                        if response.text:
                            dict_response = json.loads(response.text)
                            # print(dict_response)
                        else:
                            continue
                        if not dict_response:
                            continue
                        list_events=dict_response.get('events')
                        if not type(list_events) == list:
                            continue
                        for each_event in list_events:
                            start_date =  datetime.fromtimestamp(int(each_event.get('startTime')/1000),pytz.timezone("Asia/Kolkata")).date()
                            index_list = (df.index[(df['date'] == start_date.strftime("%d-%m-%Y")) & (df['EmpCode'] == each_person['emp_code'])].tolist())
                            if index_list and each_person:
                                index = index_list.pop()
                                df.at[index,'OutTime(HH:MM)']= datetime.fromtimestamp(int(each_event.get('startTime')/1000),pytz.timezone("Asia/Kolkata")).strftime('%H:%M')
                            elif each_person:
                                df = df.append({
                                'date':start_date.strftime("%d-%m-%Y"),
                                'EmpCode':each_person['emp_code'],
                                'InTime(HH:MM)':datetime.fromtimestamp(int(each_event.get('startTime')/1000),pytz.timezone("Asia/Kolkata")).strftime('%H:%M'),
                                'OutTime(HH:MM)':datetime.fromtimestamp(int(each_event.get('startTime')/1000),pytz.timezone("Asia/Kolkata")).strftime('%H:%M'),
                                'BiometricDate':'t'
                                },ignore_index = True)
                csv_dir = request.POST.get('path')
                df.to_csv(os.path.join(csv_dir,'exportattendance.csv') if csv_dir else '/home/user/workspace/attendance/exportattendance.csv', encoding='utf-8', index=False)

            except Exception as e:
                print(e,'line number of error {}'.format(sys.exc_info()[-1].tb_lineno))

            return HttpResponseRedirect(reverse('create_attendance_csv'))
        return render(request,'cron_create_attendance_csv.html')

    except Exception as e:
        print(e,'line number {}'.format(sys.exc_info()[-1].tb_lineno))


def create_employee(request):
    try:
        if request.method == "POST":
            print(request.POST)
            print(request.FILES)
            photo = request.FILES['profile']
            b = photo.read()
            image = base64.b64encode(b).decode("utf-8")
            firstname = request.POST.get('firstname')
            middlename = request.POST.get('middlename')
            lastname = request.POST.get('lastname')
            position_type = request.POST.get('position_type') 
            joiningdate = request.POST.get('joiningdate')
            confirmationdate = request.POST.get('confirmationdate')
            esic_location = request.POST.get('esic_location')
            site = request.POST.get('site')
            site_location = request.POST.get('site_location')
            print(site_location)
            print(firstname,middlename,lastname,position_type,joiningdate,confirmationdate,esic_location,site_location)
            hr_executive = request.POST.get('hr_executive')
            department = request.POST.get('department')
            reporting = request.POST.get('reporting')
            designation = request.POST.get('designation')
            grade = request.POST.get('grade')
            notice_period = request.POST.get('notice_period')
            father_name = request.POST.get('father_name')
            current_address = request.POST.get('current_address')
            mother_name = request.POST.get('mother_name')
            filladdress = request.POST.get('filladdress')
            permanent_address = request.POST.get('permanent_address')
            spouse_name = request.POST.get('spouse_name')
            personal_email = request.POST.get('personal_email')
            gender = request.POST.get('gender')
            personal_mobile = request.POST.get('personal_mobile')
            marital = request.POST.get('marital')
            country_id = request.POST.get('country_id')
            bank_id = request.POST.get('bank_id')
            state_id = request.POST.get('state_id')
            account_number = request.POST.get('account_number')
            pan_number = request.POST.get('pan_number')
            branch_name = request.POST.get('branch_name')
            aadhar_number = request.POST.get('aadhar_number')
            ifsc_code = request.POST.get('ifsc_code')
            passport_no = request.POST.get('passport_no')
            passport_expire_date = request.POST.get('passport_expire_date')
            visa_no = request.POST.get('visa_no')
            visa_expire_date = request.POST.get('visa_expire_date')
            company_id = request.POST.get('company_id')
            shift_id = request.POST.get('shift_id')
            total_experience = request.POST.get('total_experience')
            work_email = request.POST.get('work_email')
            highest_qualification = request.POST.get('highest_qualification')
            work_phone = request.POST.get('work_phone')
            weekly_off = request.POST.get('weekly_off')
            alternate_phone = request.POST.get('alternate_phone')
            appraisal_cycle = request.POST.get('appraisal_cycle')
            cost_center_name = request.POST.get('cost_center_name')
            category_id = request.POST.get('category_id')
            blood_group = request.POST.get('blood_group')
            emergency_contact_name = request.POST.get('emergency_contact_name')
            emergency_contact_number = request.POST.get('emergency_contact_number')
            previous_company_name = request.POST.get('previous_company_name')
            previous_designation = request.POST.get('previous_designation')
            emergency_contact_relation = request.POST.get('emergency_contact_relation')
            total_experience = request.POST.get('total_experience')
            user_id = request.POST.get('user_id')
            address_id = request.POST.get('address_id')
            address_home_id = request.POST.get('address_home_id')
            employee_billing = request.POST.get('employee_billing')
            physically_disabled = request.POST.get('physically_disabled')
            date_of_birth = request.POST.get('physically_disabled')
            filladdress = request.POST.get('date_of_birth')
            date = datetime.strptime(date_of_birth,'%Y-%m-%d')
            print(firstname+''+middlename+''+lastname)
            if middlename == '':
                name = firstname+' '+lastname
            else:
                name = firstname+' '+middlename+' '+lastname
            print(name)
            print(hr_executive,department,reporting,designation,grade,notice_period,father_name,mother_name,marital,current_address)

            id = models.execute_kw(db, uid, password, 'hr.employee', 'create', [{ 'name':name,'face_img':image,'physically_disabled':physically_disabled,'same_as_current':filladdress,'birthday':date,
            'image':image,'first_name':firstname,'middle_name':middlename,'last_name':lastname,'position_type':position_type,'joining_date':joiningdate,'confirmation_date':confirmationdate,
            'esic_location':esic_location,'site_master_id':site,'department_id':department,'job_id':designation,'hr_executive_id':hr_executive,'parent_id':reporting,
            'grade_id':grade,'notice_period':notice_period,'father_name':father_name,'mother_name':mother_name,'spouse_name':spouse_name,'gender':gender,'marital':marital,
            'blood_group':blood_group,'address':current_address,'per_address':permanent_address,'personal_email':personal_email,'personal_mobile':personal_mobile,'emergency_contact_name':emergency_contact_name,
            'emergency_contact_number':emergency_contact_number,'emergency_contact_relation':emergency_contact_relation,'country_id':country_id,'state_id':state_id,'pan':pan_number,'aadhar':aadhar_number,
            'bank_id':bank_id,'bank_account_number':account_number,'branch_name':branch_name,'ifsc_code':ifsc_code,'passport_id':passport_no,'passport_expire_date':passport_expire_date,'visa_no':visa_no,
            'visa_expire':visa_expire_date,'company_id':company_id,'site_location_id':site_location,'work_email':work_email,'work_phone':work_phone,'cost_center_id':cost_center_name,'emp_category':category_id,
            'shift_id':shift_id,'experiance_id':total_experience,'highest_qualification':highest_qualification,'weekly_off':weekly_off,'appraisal_cycle':appraisal_cycle,'previous_company':previous_company_name,
            'previous_designation':previous_designation,'employee_billing_status':employee_billing,'user_id':user_id,'address_id':address_id,'address_home_id':address_home_id}])
            
            return HttpResponseRedirect(reverse('create_employee_profile'))
        else:
            current_user = request.user
            user_id = current_user.id
            user = User.objects.get(id=user_id)
            emp_code = RegisterModel.objects.get(user=user).employee_code
            print(emp_code)
            name_ids = models.execute_kw(db, uid, password,
            'hr.employee', 'search',
            [[['emp_code','=',emp_code,]]],)
            print(type(name_ids))
            name = models.execute_kw(db, uid, password,
            'hr.employee', 'read',
            [name_ids],{'fields': ['name','image']})
            for i in name:
                emp_name = {'name':i['name'],'image':i['image']}
            emp_ids = models.execute_kw(db, uid, password,'hr.employee', 'search',[[]],)
            position_type = models.execute_kw(db, uid, password,'hr.employee', 'read',[emp_ids],{'fields': ['position_type']})
            city_ids = models.execute_kw(db, uid, password,'res.city', 'search',[[]],)
            esic_location = models.execute_kw(db, uid, password,'res.city', 'read',[city_ids],{'fields': ['name']})
            site_ids = models.execute_kw(db, uid, password,'site.master', 'search',[[]],)
            site = models.execute_kw(db, uid, password,'site.master', 'read',[city_ids],{'fields': ['name']})
            hr_name = models.execute_kw(db, uid, password,'hr.employee', 'read',[emp_ids],{'fields': ['name']})
            demp_ids = models.execute_kw(db, uid, password,'hr.department', 'search',[[]],)
            department = models.execute_kw(db, uid, password,'hr.department', 'read',[demp_ids],{'fields': ['name']})
            job_ids = models.execute_kw(db, uid, password,'hr.job', 'search',[[]],)
            job = models.execute_kw(db, uid, password,'hr.job', 'read',[job_ids],{'fields': ['name']})
            garde_ids = models.execute_kw(db, uid, password,'hr.employee.grade', 'search',[[]],)
            grade = models.execute_kw(db, uid, password,'hr.employee.grade', 'read',[demp_ids],{'fields': ['name']})
            country_ids = models.execute_kw(db, uid, password,'res.country', 'search',[[]],)
            country = models.execute_kw(db, uid, password,'res.country', 'read',[country_ids],{'fields': ['name','code']})
            state_ids = models.execute_kw(db, uid, password,'res.state', 'search',[[]],)
            state = models.execute_kw(db, uid, password,'res.state', 'read',[state_ids],{'fields': ['name']})
            bank_ids = models.execute_kw(db, uid, password,'bank.name', 'search',[[]],)
            print(bank_ids)
            bank = models.execute_kw(db, uid, password,'bank.name', 'read',[bank_ids],{'fields': ['name']})
            print(bank)
            company_id = models.execute_kw(db, uid, password,'res.company', 'search',[[]],)
            company = models.execute_kw(db, uid, password,'res.company', 'read',[company_id],{'fields': ['name']})
            shift_id = models.execute_kw(db, uid, password,'hr.employee.shift.timing', 'search',[[]],)
            shift = models.execute_kw(db, uid, password,'hr.employee.shift.timing', 'read',[shift_id],{'fields': ['name']})
            experiance_id = models.execute_kw(db, uid, password,'service.experiance', 'search',[[]],)
            experiance = models.execute_kw(db, uid, password,'service.experiance', 'read',[experiance_id],{'fields': ['experiance']})
            cost_id = models.execute_kw(db, uid, password,'cost.center', 'search',[[]],)
            cost = models.execute_kw(db, uid, password,'cost.center', 'read',[experiance_id],{'fields': ['name']})
            holiday_ids =  models.execute_kw(db, uid, password,'holiday.master', 'search',[[]],)
            holidays  = models.execute_kw(db, uid, password,'holiday.master', 'read',[holiday_ids],{'fields': ['name','holiday_date','active']})
            holiday_list = []
            for i in holidays:
                holiday = {'holiday_name':i['name'],'holiday_date':i['holiday_date']}
                holiday['days'] = datetime.strptime(i['holiday_date'], '%Y-%m-%d').strftime('%A')
                active = ''
                if i['active'] == True:
                    active = 'checked'
                else:
                    active = ''
                holiday['active'] = active
                holiday_list.append(holiday)
            user_ids = models.execute_kw(db, uid, password,'res.users', 'search',[[]],)
            user_id = models.execute_kw(db, uid, password,'res.users', 'read',[user_ids],{'fields': ['name']})
            print('user id',user_id)
            work_address_ids = models.execute_kw(db, uid, password,'res.partner', 'search',[[]],)
            work_address = models.execute_kw(db, uid, password,'res.partner', 'read',[work_address_ids],{'fields': ['name']})
            print('address',work_address)
            print(('billable', 'Billable'),('non_billable', 'Non-Billable'),'po_received','employee_billing_status')
            
            context = {'esic_location':esic_location,'site':site,'hr_name':hr_name,'department':department,'job':job,'grade':grade,
              'country':country,'state':state,'bank':bank,'company':company,'shift':shift,'experiance':experiance,'cost':cost,
              'holiday':holiday_list,'user_id':user_id,'work_address':work_address,'emp_name':emp_name}
            print(type(context))
            return render(request,'create_employee_profile.html',context)

    except Exception as e:
        print(e,'line number {}'.format(sys.exc_info()[-1].tb_lineno))


def user_profile(request):
    try:
        current_user = request.user
        user_id = current_user.id
        user = User.objects.get(id=user_id)
        emp_code = RegisterModel.objects.get(user=user).employee_code
        print('employee code',emp_code)
        ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',emp_code,]]],)

        detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [ids],{'fields': ['child_ids','name','image']})
        child_list = []
        emp_name = {}
        for i in detail:
            emp_name = {'name':i['name'],'image':i['image']}
        emp_ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',emp_code]]],)
        emp_detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [emp_ids],{'fields': ['personal_email','personal_mobile','name','department_id','category_ids','grade_id',
        'job_id','message_needaction','inactive','parent_id','coach_id','department_id','company_id',
        'emp_code','image','position_type','joining_date','confirmation_date','esic_location','site_master_id',
        'notice_period','father_name','address','mother_name','same_as_current','spouse_name','gender',
        'marital','emergency_contact_name','birthday','emergency_contact_number','physically_disabled',
        'blood_group','country_id','bank_id','state_id','bank_account_number','pan','branch_name','aadhar','ifsc_code',
        'passport_id','passport_expire_date','visa_no','visa_expire','per_address','emergency_contact_relation','site_location_id','work_email','work_phone','cost_center_id',
        'emp_category','mobile_phone','shift_id','experiance_id','highest_qualification','weekly_off','appraisal_cycle','previous_company','previous_designation','pf_uan_no','esic_uan_no',
        'user_id','address_id','address_home_id','barcode','employee_billing_status','po_received','person_id','esic_location','site_master_id','hr_executive_id']})
        
        holiday_ids =  models.execute_kw(db, uid, password,'holiday.master', 'search',[[]],)
        holidays  = models.execute_kw(db, uid, password,'holiday.master', 'read',[holiday_ids],{'fields': ['name','holiday_date','active']})
        holiday_list = []
        for i in holidays:
            holiday = {'holiday_name':i['name'],'holiday_date':i['holiday_date']}
            holiday['days'] = datetime.strptime(i['holiday_date'], '%Y-%m-%d').strftime('%A')
            active = ''
            if i['active'] == True:
                active = 'checked'
            else:
                active = ''
            holiday['active'] = active

            holiday_list.append(holiday)
        # print(emp_detail)
        # emp_details = []
        # profile_detail = []
        for i in emp_detail:
            esic_location = i['esic_location']
            if esic_location == False:
                esic_location = ''
            else :
                esic_location = esic_location[1]
            print('locations',esic_location)
            same_as_current = i['same_as_current']
            # print(i['same_as_current'])
            profile_details = {'emp_code':i['emp_code'],'name':i['name'],'grade':i['grade_id'][1],'dempartment':i['department_id'][1],'designation':i['job_id'][1],
            'reporting':i['parent_id'][1],'joining_date':i['joining_date'],'confirmation_date':i['confirmation_date'],'status':i['position_type'],'notice':i['notice_period'],'esic_location':esic_location,'site_master_id':i['site_master_id'][1],
            'hr_executive_id':i['hr_executive_id'][1]}
            image1 = i['image']
            if image1 != False:
                b = base64.b64decode(image1)
                image =  base64.b64encode(b).decode("utf-8")
                profile_details['image'] = image
            else:
                profile_details['image'] = image1
            spouse_name = i['spouse_name']
            if spouse_name == False:
                spouse_name = ''
            emergency_contact_name = i['emergency_contact_name']
            if emergency_contact_name == False:
                emergency_contact_name = ''
            emergency_contact_relation = i['emergency_contact_relation']
            if emergency_contact_relation == False:
                emergency_contact_relation = ''

            bank_id = i['bank_id']
            if bank_id == False:
                bank_id = ''
            branch_name = i['branch_name']
            if branch_name == False:
                branch_name = ''
            ifsc_code = i['ifsc_code']
            if ifsc_code == False:
                ifsc_code = ''
            passport_id = i['passport_id']
            if passport_id == False:
                passport_id = ''
            passport_expire_date = i['passport_expire_date']
            if passport_expire_date == False:
                passport_expire_date = ''
            visa_no = i['visa_no']
            if visa_no == False:
                visa_no = ''
            visa_expire = i['visa_expire']
            if visa_expire == False:
                visa_expire = ''

            work_phone = i['work_phone']
            if work_phone == False:
                work_phone = ''
            weekly_off = i['weekly_off']
            if weekly_off == False:
                weekly_off = ''
            appraisal_cycle = i['appraisal_cycle']
            if appraisal_cycle == False:
                appraisal_cycle = ''
            previous_company = i['previous_company']
            if previous_company == False:
                previous_company = ''
            previous_designation = i ['previous_designation']
            if previous_designation == False:
                previous_designation = ''
            # profile_detail.append(profile_details)
            blood = i['blood_group']
            if blood =='a_negative':
                blood_group = 'A-ve'
            elif blood == 'a_positive':
                blood_group = 'A+ve'
            elif blood == 'b_positive':
                blood_group = 'B+ve' 
            elif blood == 'b_negative':
                blood_group = 'B-ve' 
            elif blood == 'ab_positive':
                blood_group = 'AB+ve' 
            elif blood == 'ab_negative':
                blood_group = 'AB-ve' 
            elif blood == 'o_positive':
                blood_group = 'O+ve'
            elif blood == 'o_negative':
                blood_group = 'O-ve'
            else:
                blood_group = 'NA'
            
            # print(same_as_current)
            if same_as_current == True:
                same = 'checked'
            else:
                same = ''
            # print(same)
            print(i['site_location_id'])
            emp = {'father_name':i['father_name'],'mother_name':i['mother_name'],'spouse_name':spouse_name,'birthday':i['birthday'],'blood_group':blood_group,
            'physicall_disabled':i['physically_disabled'],'gender':i['gender'],'marital':i['marital'],'address':i['address'],'same':same,'per_address':i['per_address'],
            'personal_email':i['personal_email'],'personal_mobile':i['personal_mobile'],'emergency_contact_name':emergency_contact_name,'emergency_contact_number':i['emergency_contact_number'],
            'emergency_contact_relation':emergency_contact_relation,'country_id':i['country_id'][1],'state_id':i['state_id'][1],'pan':i['pan'],'aadhar':i['aadhar'],'bank_id':bank_id,
            'bank_account_number':i['bank_account_number'],'branch_name':branch_name,'ifsc_code':ifsc_code,'passport_id':passport_id,'passport_expire_date':passport_expire_date,
            'visa_no':visa_no,'visa_expire':visa_expire,'company_id':i['company_id'][1],'site_master_id':i['site_master_id'][1],'work_email':i['work_email'],'work_phone':work_phone,
            'cost_center_id':i['cost_center_id'][1],'emp_category':i['emp_category'],'mobile_phone':i['mobile_phone'],'shift_id':i['shift_id'][1],'experiance_id':i['experiance_id'][1],
            'highest_qualification':i['highest_qualification'],'weekly_off':weekly_off,'appraisal_cycle':appraisal_cycle,'previous_company':previous_company,'previous_designation':previous_designation,
            'position_type':i['position_type'],'esic_uan_no':i['esic_uan_no'],'user_id':i['user_id'][1],'address_id':i['address_id'][1],'address_home_id':i['address_home_id'],'barcode':i['barcode'],
            'employee_billing_status':i['employee_billing_status'],'po_received':i['po_received'],'person_id':i['person_id']} 

        emp_ids = models.execute_kw(db, uid, password,'hr.employee', 'search',[[]],)
        city_ids = models.execute_kw(db, uid, password,'res.city', 'search',[[]],)
        esic_location = models.execute_kw(db, uid, password,'res.city', 'read',[city_ids],{'fields': ['name']})
        site_ids = models.execute_kw(db, uid, password,'site.master', 'search',[[]],)
        site = models.execute_kw(db, uid, password,'site.master', 'read',[city_ids],{'fields': ['name']})
        hr_name = models.execute_kw(db, uid, password,'hr.employee', 'read',[emp_ids],{'fields': ['name']})
        demp_ids = models.execute_kw(db, uid, password,'hr.department', 'search',[[]],)
        department = models.execute_kw(db, uid, password,'hr.department', 'read',[demp_ids],{'fields': ['name']})
        job_ids = models.execute_kw(db, uid, password,'hr.job', 'search',[[]],)
        job = models.execute_kw(db, uid, password,'hr.job', 'read',[job_ids],{'fields': ['name']})
        garde_ids = models.execute_kw(db, uid, password,'hr.employee.grade', 'search',[[]],)
        grade = models.execute_kw(db, uid, password,'hr.employee.grade', 'read',[demp_ids],{'fields': ['name']})
        country_ids = models.execute_kw(db, uid, password,'res.country', 'search',[[]],)
        country = models.execute_kw(db, uid, password,'res.country', 'read',[country_ids],{'fields': ['name','code']})
        state_ids = models.execute_kw(db, uid, password,'res.state', 'search',[[]],)
        state = models.execute_kw(db, uid, password,'res.state', 'read',[state_ids],{'fields': ['name']})
        bank_ids = models.execute_kw(db, uid, password,'bank.name', 'search',[[]],)
        bank = models.execute_kw(db, uid, password,'bank.name', 'read',[bank_ids],{'fields': ['name']})
        company_id = models.execute_kw(db, uid, password,'res.company', 'search',[[]],)
        company = models.execute_kw(db, uid, password,'res.company', 'read',[company_id],{'fields': ['name']})
        shift_id = models.execute_kw(db, uid, password,'hr.employee.shift.timing', 'search',[[]],)
        shift = models.execute_kw(db, uid, password,'hr.employee.shift.timing', 'read',[shift_id],{'fields': ['name']})
        experiance_id = models.execute_kw(db, uid, password,'service.experiance', 'search',[[]],)
        experiance = models.execute_kw(db, uid, password,'service.experiance', 'read',[experiance_id],{'fields': ['experiance']})
        cost_id = models.execute_kw(db, uid, password,'cost.center', 'search',[[]],)
        cost = models.execute_kw(db, uid, password,'cost.center', 'read',[experiance_id],{'fields': ['name']})
        holiday_ids =  models.execute_kw(db, uid, password,'holiday.master', 'search',[[]],)
        holidays  = models.execute_kw(db, uid, password,'holiday.master', 'read',[holiday_ids],{'fields': ['name','holiday_date','active']})
        user_ids = models.execute_kw(db, uid, password,'res.users', 'search',[[]],)
        user_id = models.execute_kw(db, uid, password,'res.users', 'read',[user_ids],{'fields': ['name']})
        print('user id',user_id)
        work_address_ids = models.execute_kw(db, uid, password,'res.partner', 'search',[[]],)
        work_address = models.execute_kw(db, uid, password,'res.partner', 'read',[work_address_ids],{'fields': ['name']})

            # emp_details.append(emp)

        context = {'profile_details':profile_details,'emp':emp,'holidays':holiday_list,'emp_name':emp_name,'esic_location':esic_location,'site':site,'hr_name':hr_name,'department':department,'job':job,
        'grade':grade,'country':country,'state':state,'bank':bank,'company':company,'shift':shift,'experiance':experiance,'cost':cost,'holiday':holidays,'user_id':user_id,'work_address':work_address}

        # print(context)
        return render(request,'user_profile.html',context)

    except Exception as e:
        print(e,'line number {}'.format(sys.exc_info()[-1].tb_lineno))


def team_employee_profile(request):
    try:
        current_user = request.user
        user_id = current_user.id
        user = User.objects.get(id=user_id)
        emp_code = RegisterModel.objects.get(user=user).employee_code
        print(emp_code)
        ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',emp_code,]]],)

        detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [ids],{'fields': ['child_ids','name','image']})
        child_list = []
        emp_name = {}
        for i in detail:
            emp_name = {'name':i['name'],'image':i['image']}
            id = i['child_ids']
            child_ids = models.execute_kw(db, uid, password,
            'hr.employee', 'search',
            [[['id','=',id,]]],)

            child_detail = models.execute_kw(db, uid, password,
            'hr.employee', 'read',
            [child_ids],{'fields': ['emp_code','name','department_id','job_id','parent_id','image']})


            child_list.append(child_detail)
        # print(child_list)
        today1 = date.today()
        today = today1.strftime("%Y-%m-%d")
        first = today1.replace(day=1)
        first1 = first.strftime("%Y-%m-%d")
        present = 0
        child = []
        for i in child_list:
            for j in i:
                
                child_emp_code = j['emp_code']
                count_ids = models.execute_kw(db, uid, password,
                'hr.attendance', 'search',
                [[['employee_code','=',child_emp_code,],['attendance_date','<=',today],['attendance_date','>=',first1]]],)
                
                count = models.execute_kw(db, uid, password,
                'hr.attendance', 'read',
                [count_ids],{'fields': ['attendance_date','worked_hours','shift','employee_status']})

                for counts in count:
                    status = counts['employee_status']

                    if status == 'P':
                        present += 1

                
                dict1 = {'name':j['name'],'emp_code':j['emp_code'],'job':j['job_id'][1],'parent':j['parent_id'][1],'present':present}
                
                image1 = j['image']
                if image1 != False:
                    # print(image1)
                    b = base64.b64decode(image1)
                    image =  base64.b64encode(b).decode("utf-8")
                    dict1['image'] = image
                else:
                    dict1['image'] = image1
                child.append(dict1)
        
        # print
        # print('dictionay',dict1)   
        # print('data stor',child)     
        demp_ids = models.execute_kw(db, uid, password,
        'hr.department', 'search',
        [[]],)

        demp_detail = models.execute_kw(db, uid, password,
        'hr.department', 'read',
        [demp_ids],{'fields': ['name']})  
         
        site_ids = models.execute_kw(db, uid, password,
        'site.master', 'search',
        [[]],)   
        site_detail = models.execute_kw(db, uid, password,
        'site.master', 'read',
        [site_ids],{'fields': ['name']})
        

        print(site_detail)
        context = {'emp_list':child,'emp_name':emp_name,'demp':demp_detail,'site':site_detail}
        # print(context)


        return render(request,'teams_employee_profile.html',context)
    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))



def search_function(request):
    try:
        print(request.GET)
        location = request.GET.get('location')
        department = request.GET.get('department')
        member = request.GET.get('member')
        current_user = request.user
        user_id = current_user.id
        user = User.objects.get(id=user_id)
        emp_code = RegisterModel.objects.get(user=user).employee_code
        print(emp_code)
        if location != None and location !='Location':
            print(type(location))
            ids = models.execute_kw(db, uid, password,
            'hr.employee', 'search',
            [[['site_master_id','=',int(location),]]],)
            # print(ids)
            child_detail = models.execute_kw(db, uid, password,
            'hr.employee', 'read',
            [ids],{'fields': ['emp_code','name','department_id','job_id','parent_id','image']})
            child_list = []
            for j in child_detail:
                dict1 = {'name':j['name'],'emp_code':j['emp_code'],'job':j['job_id'][1],'parent':j['parent_id'][1]}
                
                image1 = j['image']
                if image1 != False:
                    # print(image1)
                    b = base64.b64decode(image1)
                    image =  base64.b64encode(b).decode("utf-8")
                    dict1['image'] = image
                else:
                    dict1['image'] = image1
                child_list.append(dict1)

            # print('this location',child_detail)
            demp_ids = models.execute_kw(db, uid, password,
            'hr.department', 'search',
            [[]],)

            demp_detail = models.execute_kw(db, uid, password,
            'hr.department', 'read',
            [demp_ids],{'fields': ['name']})
            site_ids = models.execute_kw(db, uid, password,
            'site.master', 'search',
            [[]],)   
            site_detail = models.execute_kw(db, uid, password,
            'site.master', 'read',
            [site_ids],{'fields': ['name']})

            name_ids = models.execute_kw(db, uid, password,
            'hr.employee', 'search',
            [[['emp_code','=',emp_code,]]],)
            detail = models.execute_kw(db, uid, password,
            'hr.employee', 'read',
            [name_ids],{'fields': ['child_ids','name','image']})
            print(detail)
            emp_name = {}
            for i in detail:
                emp_name = {'name':i['name'],'image':i['image']}


            context = {'emp_list':child_list,'emp_name':emp_name,'demp':demp_detail,'site':site_detail}

            return render(request,'search_page.html',context)

        if department != None and department != 'Department':
            ids = models.execute_kw(db, uid, password,
            'hr.employee', 'search',
            [[['department_id','=',int(department),]]],)
            child_detail = models.execute_kw(db, uid, password,
            'hr.employee', 'read',
            [ids],{'fields': ['emp_code','name','department_id','job_id','parent_id','image']})

            child_list = []
            for j in child_detail:
                dict1 = {'name':j['name'],'emp_code':j['emp_code'],'job':j['job_id'][1],'parent':j['parent_id'][1]}
                
                image1 = j['image']
                if image1 != False:
                    # print(image1)
                    b = base64.b64decode(image1)
                    image =  base64.b64encode(b).decode("utf-8")
                    dict1['image'] = image
                else:
                    dict1['image'] = image1
                child_list.append(dict1)

            demp_ids = models.execute_kw(db, uid, password,
            'hr.department', 'search',
            [[]],)

            demp_detail = models.execute_kw(db, uid, password,
            'hr.department', 'read',
            [demp_ids],{'fields': ['name']})
            site_ids = models.execute_kw(db, uid, password,
            'site.master', 'search',
            [[]],)   
            site_detail = models.execute_kw(db, uid, password,
            'site.master', 'read',
            [site_ids],{'fields': ['name']})

            name_ids = models.execute_kw(db, uid, password,
            'hr.employee', 'search',
            [[['emp_code','=',emp_code,]]],)
            detail = models.execute_kw(db, uid, password,
            'hr.employee', 'read',
            [name_ids],{'fields': ['child_ids','name','image']})
            emp_name = {}
            for i in detail:
                emp_name = {'name':i['name'],'image':i['image']}
            
            context = {'emp_list':child_list,'emp_name':emp_name,'demp':demp_detail,'site':site_detail}

            return render(request,'search_page.html',context)

        if member != None and member != 'Employee':
            ids = models.execute_kw(db, uid, password,
            'hr.employee', 'search',
            [[['emp_code','=',int(member),]]],)
            child_detail = models.execute_kw(db, uid, password,
            'hr.employee', 'read',
            [ids],{'fields': ['emp_code','name','department_id','job_id','parent_id','image']})
            child_list = []
            for j in child_detail:
                dict1 = {'name':j['name'],'emp_code':j['emp_code'],'job':j['job_id'][1],'parent':j['parent_id'][1]}
                
                image1 = j['image']
                if image1 != False:
                    # print(image1)
                    b = base64.b64decode(image1)
                    image =  base64.b64encode(b).decode("utf-8")
                    dict1['image'] = image
                else:
                    dict1['image'] = image1
                child_list.append(dict1)

            demp_ids = models.execute_kw(db, uid, password,
            'hr.department', 'search',
            [[]],)

            demp_detail = models.execute_kw(db, uid, password,
            'hr.department', 'read',
            [demp_ids],{'fields': ['name']})
            site_ids = models.execute_kw(db, uid, password,
            'site.master', 'search',
            [[]],)   
            site_detail = models.execute_kw(db, uid, password,
            'site.master', 'read',
            [site_ids],{'fields': ['name']})

            name_ids = models.execute_kw(db, uid, password,
            'hr.employee', 'search',
            [[['emp_code','=',emp_code,]]],)
            detail = models.execute_kw(db, uid, password,
            'hr.employee', 'read',
            [name_ids],{'fields': ['child_ids','name','image']})
            child_list1 = []
            emp_name = {}
            for i in detail:
                emp_name = {'name':i['name'],'image':i['image']}
                id = i['child_ids']
                child_ids1 = models.execute_kw(db, uid, password,
                'hr.employee', 'search',
                [[['id','=',id,]]],)

                child_detail1 = models.execute_kw(db, uid, password,
                'hr.employee', 'read',
                [child_ids1],{'fields': ['emp_code','name']})
                child_list1.append(child_detail1)
            child = []
            for i in child_list1:
                for j in i:
                    dict1 = {'name':j['name'],'emp_code':j['emp_code']}
                    child.append(dict1)

            
            context = {'emp_list':child_list,'emp_name':emp_name,'demp':demp_detail,'site':site_detail,'child_name':child}
            return render(request,'search_page.html',context)

        else:
            return HttpResponse('please select valid failed')
        

        # return HttpResponse(request.GET)
    
    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))



def search_attendance(request):
    try:
        
        print(request.GET)    
        child_emp_code = request.GET.get('member')
        if child_emp_code != None and child_emp_code != 'Employee':
            current_user = request.user
            user_id = current_user.id
            user = User.objects.get(id=user_id)
            emp_code = RegisterModel.objects.get(user=user).employee_code
            print(emp_code)

            from_zone = tz.gettz('UTC')
            to_zone = tz.gettz('Asia/Kolkata')
            ids = models.execute_kw(db, uid, password,
            'hr.employee', 'search',
            [[['emp_code','=',emp_code,]]],)

            detail = models.execute_kw(db, uid, password,
            'hr.employee', 'read',
            [ids],{'fields': ['name','image','child_ids']})
            child_list = []
            emp_name = {}
            for i in detail:
                emp_name = {'name':i['name'],'image':i['image']}
                id = i['child_ids']
                child_ids = models.execute_kw(db, uid, password,
                'hr.employee', 'search',
                [[['id','=',id,]]],)

                child_detail = models.execute_kw(db, uid, password,
                'hr.employee', 'read',
                [child_ids],{'fields': ['emp_code','name',]})
                print(child_detail)
                for j in child_detail:
                    temp = {'emp_code':j['emp_code'],'name':j['name']}
                    child_list.append(temp)
                    print(temp)

            # cron job for import safr attendaces data #############################
            # models.execute_kw(db, uid, password,
            # 'ir.cron', 'method_direct_trigger',[[]],)

            # models.execute_kw(db,uid,password,
            # 'safr.attendance.records','cron_safr_import_attendance_master',[[]])
            #############################################end cron ###############
            #for today attendaces
            print(child_list)
            demp_ids = models.execute_kw(db, uid, password,
            'hr.department', 'search',
            [[]],)

            demp_detail = models.execute_kw(db, uid, password,
            'hr.department', 'read',
            [demp_ids],{'fields': ['name']})
            today = date.today()
            today = today.strftime("%Y-%m-%d")
            todays_ids = models.execute_kw(db, uid, password,
            'hr.attendance', 'search',
            [[['employee_code','=',child_emp_code],['attendance_date','=',today]]],)
            days = date.today().strftime('%A')
            today_details = emp_detail = models.execute_kw(db, uid, password,
            'hr.attendance', 'read',
            [todays_ids],{'fields': ['employee_code','attendance_date','in_time','out_time','worked_hours','employee_status','import_status','source_id_in','source_id_out']})
            print(today_details)
            today_atte = []
            today_atte_data = {}
            for i in today_details:
                status = i['employee_status']
                if status == 'AB':
                    status = 'Absent'
                elif status == 'P':
                    status = 'Present'
                elif status == 'half_day_p_ab':
                    status = 'Half Day'
                today_atte_data = {'employee_code':i['employee_code'],'attendance_date':i['attendance_date'],'import_status':i['import_status'],'check_in':i['in_time'],'check_out':i['out_time'],
                'source_id_in':i['source_id_in'],'source_id_out':i['source_id_out'],'status':status,'worked_hours':i['worked_hours']}


            image_ids = models.execute_kw(db, uid, password,
            'hr.employee', 'search',
            [[['emp_code','=',child_emp_code,]]],)
            
            image_detail = models.execute_kw(db, uid, password,
            'hr.employee', 'read',
            [image_ids],{'fields': ['image','emp_code','name','shift_id']})
            img_list = []
            shift = []
            for i in image_detail:
                emp_dict = {'name':i['name'],'emp_code':i['emp_code']}
                shift_id = i['shift_id']
                # print(shift_id)
                shift.append(shift_id)
                image1 = i['image']
                if image1 != False:
                    b = base64.b64decode(image1)
                    # print(img)
                    # img = Image.open(io.BytesIO(b))
                    image =  base64.b64encode(b).decode("utf-8")
                    # img.show()
                    # img_list.append(image)
                    emp_dict['image'] = image
                else:
                    # img_list.append(image1)
                    emp_dict['image'] = image1
                img_list.append(emp_dict)
            holidays_ids = models.execute_kw(db, uid, password,
            'hr.holidays', 'search',
            [[['employee_code','=',child_emp_code,]]],)

            holidays_detail = models.execute_kw(db, uid, password,
            'hr.holidays', 'read',
            [holidays_ids],{'fields': ['total_days','holiday_status_id','date_from_new','date_to_new']})
            print(holidays_detail)


            emp_ids = models.execute_kw(db, uid, password,
            'hr.attendance', 'search',
            [[['employee_code','=',child_emp_code,]]],)

            atten_detail = models.execute_kw(db, uid, password,
            'hr.attendance', 'read',
            [emp_ids],{'fields': ['attendance_date','in_time','out_time','worked_hours','shift','employee_status']})
            
            
            present = 0
            absent = 0
            half_day = 0 
            today1 = date.today()
            print(present,absent)
            first = today1.replace(day=1)
            first1 = first.strftime("%Y-%m-%d")
            print(first)
            count_ids = models.execute_kw(db, uid, password,
            'hr.attendance', 'search',
            [[['employee_code','=',child_emp_code],['attendance_date','<=',today],['attendance_date','>=',first1]]],)
            count = models.execute_kw(db, uid, password,
            'hr.attendance', 'read',
            [count_ids],{'fields': ['attendance_date','in_time','out_time','worked_hours','shift','employee_status']})
            for i in count:
                status = i['employee_status']
                if status == 'AB':
                    absent += 1
                elif status == 'P':
                    present += 1
                elif status == 'half_day_p_ab':
                    half_day += 1
            attend_list = []
            for i in atten_detail:
                status = i['employee_status']
                if status == 'AB':
                    status = 'Absent'
                elif status == 'P':
                    status = 'Present'
                elif status == 'half_day_p_ab':
                    status = 'Half Day'
                emp_dict = {'attendance_date':i['attendance_date'],'check_in':i['in_time'],'check_out':i['out_time'],'status':status,'worked_hours':i['worked_hours']}
                attend_list.append(emp_dict)
            site_ids = models.execute_kw(db, uid, password,
            'site.master', 'search',
            [[]],)   
            site_detail = models.execute_kw(db, uid, password,
            'site.master', 'read',
            [site_ids],{'fields': ['name']})
            demp_ids = models.execute_kw(db, uid, password,
            'hr.department', 'search',
            [[]],)

            demp_detail = models.execute_kw(db, uid, password,
            'hr.department', 'read',
            [demp_ids],{'fields': ['name']})
            last = last_day_of_month(today1)
            print(last)
            print(today_atte,days)
            context = {'image':img_list,'emp':emp_detail,'today_atte':today_atte_data,'days':days,'firstday':first,'lastday':last,'attendance':attend_list,
            'present':present,'absent':absent,'half_day':half_day,'emp_name':emp_name,'child_list':child_list,'demp':demp_detail,'site':site_detail}
            # print(context)
            return render(request,'search_attendance_member.html',context)
        else :
            return  HttpResponse('PLease select valid field')


    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))

@csrf_exempt
def save_basic_info(request):
    try:
        print(request.method)
        print(request.POST)
        if request.method == 'POST':
            print(request.POST)
            fathername = request.POST.get('fathername')
            print('working')
            messages.error(request,'please enable edit button')
            
            
            return redirect('/user_profile/')
            # return HttpResponse('woking')
            

    except Exception as e:
        print(e,'line number {}'.format(sys.exc_info()[-1].tb_lineno)) 



def master_table(request):
    try:
        print('working')
        current_user = request.user
        user_id = current_user.id
        user = User.objects.get(id=user_id)
        emp_code = RegisterModel.objects.get(user=user).employee_code
        print('employee code',emp_code)
        ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',emp_code,]]],)
        
        print(ids)
    
        hr_details = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['hr_executive_id','=',ids,]]],)

        hr_emp_code = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [hr_details],{'fields': ['name','emp_code','child_ids']})

        print(hr_emp_code)
        print(hr_details)

        detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [ids],{'fields': ['name','image','child_ids']})
        child_list = []
        emp_name = {}
        for i in detail:
            print(i['child_ids'])
            emp_name = {'name':i['name'],'image':i['image']}

        holiday_ids =  models.execute_kw(db, uid, password,'holiday.master', 'search',[[]],)
        holidays  = models.execute_kw(db, uid, password,'holiday.master', 'read',[holiday_ids],{'fields': ['name','holiday_date','active']})
        
        department_ids  = models.execute_kw(db, uid, password,'hr.department', 'search',[[]],)
        department = models.execute_kw(db, uid, password,'hr.department', 'read',[department_ids],{'fields': ['display_name','manager_id','parent_id','active']})
        shift_ids = models.execute_kw(db, uid, password,'hr.employee.shift.timing', 'search',[[]],)
        shift = models.execute_kw(db, uid, password,'hr.employee.shift.timing', 'read',[shift_ids],{'fields': ['name','in_shift_time','out_shift_time',]})
        state_ids = models.execute_kw(db, uid, password,'res.state', 'search',[[]],)
        state = models.execute_kw(db, uid, password,'res.state', 'read',[state_ids],{'fields': ['name','active','union_territory']})
        cost_ids = models.execute_kw(db, uid, password,'cost.center', 'search',[[]],)
        cost = models.execute_kw(db, uid, password,'cost.center', 'read',[cost_ids],{'fields': ['name']})
        
        site_ids = models.execute_kw(db, uid, password,'site.master', 'search',[[]],)
        site = models.execute_kw(db, uid, password,'site.master', 'read',[site_ids],{'fields': ['name','active']})
        
        site_location_ids = models.execute_kw(db, uid, password,'res.city', 'search',[[]],)
        site_location = models.execute_kw(db, uid, password,'res.city', 'read',[site_location_ids],{'fields': ['name','state','active']})

        job_ids = models.execute_kw(db, uid, password,'hr.job', 'search',[[]],)
        job = models.execute_kw(db, uid, password,'hr.job', 'read',[job_ids],{'fields': ['name','state','active']})

        site_location_list = []
        for i in site_location:
            site_location = {'name':i['name'],'state':i['state'][1]}
            if i['active'] == True:
                active = 'checked'
            site_location['active'] = active
            site_location_list.append(site_location)

        site_list = []
        for i in site:
            site = {'name':i['name']}
            if i['active'] == True:
                active = 'checked'
            site['active'] = active
            site_list.append(site)
        state_list = []
        for i in state:
            state = {'name':i['name'],'id':i['id']}
            active = ''
            if i['active'] == True:
                active = 'checked'
            state['active'] = active

            union_territory = ''
            if i['union_territory'] == True:
                union_territory = 'checked'
            state['union_territory'] = union_territory

            state_list.append(state)
            
        department_list = []
        for i in department:
            department = {'display_name':i['display_name'],'manager_id':i['manager_id'],'parent_id':i['parent_id']}
            active = ''
            if i['active'] == True:
                active = 'checked'
            else:
                active = ''
            department['active'] = active
            department_list.append(department)

        holiday_list = []
        for i in holidays:
            holiday = {'holiday_name':i['name'],'holiday_date':i['holiday_date']}
            holiday['days'] = datetime.strptime(i['holiday_date'], '%Y-%m-%d').strftime('%A')
            active = ''
            if i['active'] == True:
                active = 'checked'
            else:
                active = ''
            holiday['active'] = active

            holiday_list.append(holiday)

        context = {'emp_name':emp_name,'holidays':holiday_list,'department':department_list,'shift':shift,'state':state_list,'const':cost,'site':site_list,'site_location':site_location_list,'job':job}
        return render(request,'master_page.html',context)
        

    except Exception as e:
        print(e,'line number {}'.format(sys.exc_info()[-1].tb_lineno))


def hr_attendance(request):
    try:
        today = date.today()
        today = today.strftime("%Y-%m-%d")
        current_user = request.user
        user_id = current_user.id
        user = User.objects.get(id=user_id)
        emp_code = RegisterModel.objects.get(user=user).employee_code
        print(emp_code)
        ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',emp_code,]]],)

        detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [ids],{'fields': ['name','image']})
        child_list = []
        emp_name = {}
        for i in detail:
            emp_name = {'name':i['name'],'image':i['image']}
        image_ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',emp_code,]]],)

        image_detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [image_ids],{'fields': ['emp_code','name','shift_id','child_ids']})

        demp_ids = models.execute_kw(db, uid, password,
        'hr.department', 'search',
        [[]],)

        demp_detail = models.execute_kw(db, uid, password,
        'hr.department', 'read',
        [demp_ids],{'fields': ['name']})
        ##################################################child details ################################
        hr_details = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['hr_executive_id','=',ids,]]],)

        hr_emp_code = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [hr_details],{'fields': ['name','emp_code',]})
        child_name = []
        for i in hr_emp_code:
            emp_dict = {'name':i['name'],'emp_code':i['emp_code']}
            child_name.append(emp_dict)
        print(child_name)
        child_emp_code = hr_emp_code[0]['emp_code']
        child_image_ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',child_emp_code]]],)

        
        
        child_image_detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [child_image_ids],{'fields': ['emp_code','name','shift_id','image']})


        child_todays_ids = models.execute_kw(db, uid, password,
        'hr.attendance', 'search',
        [[['employee_code','=',child_emp_code],['attendance_date','=',today]]],)

        child_today_details = models.execute_kw(db, uid, password,
        'hr.attendance', 'read',
        [child_todays_ids],{'fields': ['employee_code','attendance_date','in_time','out_time','worked_hours','employee_status','import_status','source_id_in','source_id_out']})
        child_today_atte = []
        child_today_data = {}
        for i in child_today_details:
            status = i['employee_status']
            if status == 'AB':
                status = 'Absent'
            elif status == 'P':
                status = 'Present'
            elif status == 'half_day_p_ab':
                status = 'Half Day'
            child_today_data = {'employee_code':i['employee_code'],'attendance_date':i['attendance_date'],'import_status':i['import_status'],'check_in':i['in_time'],'check_out':i['out_time'],
            'source_id_in':i['source_id_in'],'source_id_out':i['source_id_out'],'status':status,'worked_hours':i['worked_hours']}
           
        child_img_list = []
        shift = []
        for i in child_image_detail:
            emp_dict = {'name':i['name'],'emp_code':i['emp_code']}
            shift_id = i['shift_id']
            shift.append(shift_id)
            image1 = i['image']
            if image1 != False:
                b = base64.b64decode(image1)
                image =  base64.b64encode(b).decode("utf-8")
                emp_dict['image'] = image
            else:
                emp_dict['image'] = image1
            child_img_list.append(emp_dict)
        child_emp_ids = models.execute_kw(db, uid, password,
        'hr.attendance', 'search',
        [[['employee_code','=',child_emp_code,]]],)

        child_atten_detail = models.execute_kw(db, uid, password,
        'hr.attendance', 'read',
        [child_emp_ids],{'fields': ['attendance_date','in_time','out_time','worked_hours','shift','employee_status',]})
        today1 = date.today()
        first = today1.replace(day=1)
        first1 = first.strftime("%Y-%m-%d")
       
        child_attend_list = []
        child_count_ids = models.execute_kw(db, uid, password,
        'hr.attendance', 'search',
        [[['employee_code','=',child_emp_code],['attendance_date','<=',today],['attendance_date','>=',first1]]],)
        child_count = models.execute_kw(db, uid, password,
        'hr.attendance', 'read',
        [child_count_ids],{'fields': ['attendance_date','in_time','out_time','worked_hours','shift','employee_status']})
        print(child_count)
        child_present = 0
        child_absent = 0
        child_half_day = 0 
        for i in child_count:
            status = i['employee_status']
            if status == 'AB':
                child_absent += 1
            elif status == 'P':
                child_present += 1
            elif status == 'half_day_p_ab':
                child_half_day += 1
        for i in child_atten_detail:
            status = i['employee_status']
            if status == 'AB':
                status = 'Absent'
            elif status == 'P':
                status = 'Present'
            elif status == 'half_day_p_ab':
                status = 'Half Day'
            emp_dict = {'attendance_date':i['attendance_date'],'check_in':i['in_time'],'check_out':i['out_time'],'status':status,'worked_hours':i['worked_hours']}
            child_attend_list.append(emp_dict)
        ##################################################################################################
        ####################################team leader #####################################
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Asia/Kolkata')
        todays_ids = models.execute_kw(db, uid, password,
        'hr.attendance', 'search',
        [[['employee_code','=',emp_code],['attendance_date','=',today]]],)
        days = date.today().strftime('%A')
        today_details = emp_detail = models.execute_kw(db, uid, password,
        'hr.attendance', 'read',
        [todays_ids],{'fields': ['employee_code','attendance_date','in_time','out_time','worked_hours','employee_status','import_status','source_id_in','source_id_out']})
        today_atte = []
        today_atte_data = {}
        for i in today_details:
            status = i['employee_status']
            if status == 'AB':
                status = 'Absent'
            elif status == 'P':
                status = 'Present'
            elif status == 'half_day_p_ab':
                status = 'Half Day'
            today_atte_data = {'employee_code':i['employee_code'],'attendance_date':i['attendance_date'],'import_status':i['import_status'],'check_in':i['in_time'],'check_out':i['out_time'],
            'source_id_in':i['source_id_in'],'source_id_out':i['source_id_out'],'status':status,'worked_hours':i['worked_hours']}


    
        image_ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['emp_code','=',emp_code,]]],)
        
        image_detail = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [image_ids],{'fields': ['image','emp_code','name','shift_id']})
        img_list = []
        shift = []
        for i in image_detail:
            emp_dict = {'name':i['name'],'emp_code':i['emp_code']}
            shift_id = i['shift_id']
            # print(shift_id)
            shift.append(shift_id)
            image1 = i['image']
            if image1 != False:
                b = base64.b64decode(image1)
                # print(img)
                # img = Image.open(io.BytesIO(b))
                image =  base64.b64encode(b).decode("utf-8")
                # img.show()
                # img_list.append(image)
                emp_dict['image'] = image
            else:
                # img_list.append(image1)
                emp_dict['image'] = image1
            img_list.append(emp_dict)

        ################################################
        holidays_ids = models.execute_kw(db, uid, password,
        'hr.holidays', 'search',
        [[['employee_code','=',emp_code,]]],)

        holidays_detail = models.execute_kw(db, uid, password,
        'hr.holidays', 'read',
        [holidays_ids],{'fields': ['total_days','holiday_status_id','date_from_new','date_to_new']})


        emp_ids = models.execute_kw(db, uid, password,
        'hr.attendance', 'search',
        [[['employee_code','=',emp_code,]]],)

        atten_detail = models.execute_kw(db, uid, password,
        'hr.attendance', 'read',
        [emp_ids],{'fields': ['attendance_date','in_time','out_time','worked_hours','shift','employee_status','site_master_id']})
        
       
        present = 0
        absent = 0
        half_day = 0 
        count_ids = models.execute_kw(db, uid, password,
        'hr.attendance', 'search',
        [[['employee_code','=',emp_code],['attendance_date','<=',today],['attendance_date','>=',first1]]],)
        count = models.execute_kw(db, uid, password,
        'hr.attendance', 'read',
        [count_ids],{'fields': ['attendance_date','in_time','out_time','worked_hours','shift','employee_status']})
       
        for i in count:
            status = i['employee_status']
            if status == 'AB':
                absent += 1
            elif status == 'P':
                present += 1
            elif status == 'half_day_p_ab':
                half_day += 1

        attend_list = []
        for i in atten_detail:
            status = i['employee_status']
            if status == 'AB':
                status = 'Absent'
            elif status == 'P':
                status = 'Present'
            elif status == 'half_day_p_ab':
                status = 'Half Day'
            emp_dict = {'attendance_date':i['attendance_date'],'check_in':i['in_time'],'check_out':i['out_time'],'status':status,'worked_hours':i['worked_hours']}
            attend_list.append(emp_dict)
    
        
        last = last_day_of_month(today1)
        context = {'image':img_list,'emp':emp_detail,'today_atte':today_atte_data,'days':days,'firstday':first,'lastday':last,'attendance':attend_list,
        'present':present,'absent':absent,'half_day':half_day,'demp':demp_detail,'child_image':child_image_detail,'child_today':child_today_data,
        'child_attendance':child_attend_list,'child_present':child_present,'child_absent':child_absent,'child_half_day':child_half_day,'emp_name':emp_name,'child_name':child_name}

        #######################################################################################

        return render(request,'hr_attendance.html',context)
        # return render(request,'')
        # return HttpResponse('working')
    except Exception as e:
        print(e,'line number {}'.format(sys.exc_info()[-1].tb_lineno))



def hr_search_attendance(request):
    try:
        
        print(request.GET)    
        child_emp_code = request.GET.get('member')
        if child_emp_code != None and child_emp_code != 'Employee':
            current_user = request.user
            user_id = current_user.id
            user = User.objects.get(id=user_id)
            emp_code = RegisterModel.objects.get(user=user).employee_code
            print(emp_code)

            from_zone = tz.gettz('UTC')
            to_zone = tz.gettz('Asia/Kolkata')
            ids = models.execute_kw(db, uid, password,
            'hr.employee', 'search',
            [[['emp_code','=',emp_code,]]],)

            detail = models.execute_kw(db, uid, password,
            'hr.employee', 'read',
            [ids],{'fields': ['name','image','child_ids']})
            hr_details = models.execute_kw(db, uid, password,
            'hr.employee', 'search',
            [[['hr_executive_id','=',ids,]]],)

            hr_emp_code = models.execute_kw(db, uid, password,
            'hr.employee', 'read',
            [hr_details],{'fields': ['name','emp_code',]})
            child_list = []
            for i in hr_emp_code:
                emp_dict = {'name':i['name'],'emp_code':i['emp_code']}
                child_list.append(emp_dict)
            emp_name = {}
            for i in detail:
                emp_name = {'name':i['name'],'image':i['image']}
            print(child_list)
            today = date.today()
            today = today.strftime("%Y-%m-%d")
            todays_ids = models.execute_kw(db, uid, password,
            'hr.attendance', 'search',
            [[['employee_code','=',child_emp_code],['attendance_date','=',today]]],)
            days = date.today().strftime('%A')
            today_details = emp_detail = models.execute_kw(db, uid, password,
            'hr.attendance', 'read',
            [todays_ids],{'fields': ['employee_code','attendance_date','in_time','out_time','worked_hours','employee_status','import_status','source_id_in','source_id_out']})
            print(today_details)
            today_atte = []
            today_atte_data = {}
            for i in today_details:
                status = i['employee_status']
                if status == 'AB':
                    status = 'Absent'
                elif status == 'P':
                    status = 'Present'
                elif status == 'half_day_p_ab':
                    status = 'Half Day'
                today_atte_data = {'employee_code':i['employee_code'],'attendance_date':i['attendance_date'],'import_status':i['import_status'],'check_in':i['in_time'],'check_out':i['out_time'],
                'source_id_in':i['source_id_in'],'source_id_out':i['source_id_out'],'status':status,'worked_hours':i['worked_hours']}


            image_ids = models.execute_kw(db, uid, password,
            'hr.employee', 'search',
            [[['emp_code','=',child_emp_code,]]],)
            
            image_detail = models.execute_kw(db, uid, password,
            'hr.employee', 'read',
            [image_ids],{'fields': ['image','emp_code','name','shift_id']})
            img_list = []
            shift = []
            for i in image_detail:
                emp_dict = {'name':i['name'],'emp_code':i['emp_code']}
                shift_id = i['shift_id']
                # print(shift_id)
                shift.append(shift_id)
                image1 = i['image']
                if image1 != False:
                    b = base64.b64decode(image1)
                    # print(img)
                    # img = Image.open(io.BytesIO(b))
                    image =  base64.b64encode(b).decode("utf-8")
                    # img.show()
                    # img_list.append(image)
                    emp_dict['image'] = image
                else:
                    # img_list.append(image1)
                    emp_dict['image'] = image1
                img_list.append(emp_dict)
            holidays_ids = models.execute_kw(db, uid, password,
            'hr.holidays', 'search',
            [[['employee_code','=',child_emp_code,]]],)

            holidays_detail = models.execute_kw(db, uid, password,
            'hr.holidays', 'read',
            [holidays_ids],{'fields': ['total_days','holiday_status_id','date_from_new','date_to_new']})
            print(holidays_detail)


            emp_ids = models.execute_kw(db, uid, password,
            'hr.attendance', 'search',
            [[['employee_code','=',child_emp_code,]]],)

            atten_detail = models.execute_kw(db, uid, password,
            'hr.attendance', 'read',
            [emp_ids],{'fields': ['attendance_date','in_time','out_time','worked_hours','shift','employee_status']})
            
            
            present = 0
            absent = 0
            half_day = 0 
            today1 = date.today()
            print(present,absent)
            first = today1.replace(day=1)
            first1 = first.strftime("%Y-%m-%d")
            print(first)
            count_ids = models.execute_kw(db, uid, password,
            'hr.attendance', 'search',
            [[['employee_code','=',child_emp_code],['attendance_date','<=',today],['attendance_date','>=',first1]]],)
            count = models.execute_kw(db, uid, password,
            'hr.attendance', 'read',
            [count_ids],{'fields': ['attendance_date','in_time','out_time','worked_hours','shift','employee_status']})
            for i in count:
                status = i['employee_status']
                if status == 'AB':
                    absent += 1
                elif status == 'P':
                    present += 1
                elif status == 'half_day_p_ab':
                    half_day += 1
            attend_list = []
            for i in atten_detail:
                status = i['employee_status']
                if status == 'AB':
                    status = 'Absent'
                elif status == 'P':
                    status = 'Present'
                elif status == 'half_day_p_ab':
                    status = 'Half Day'
                emp_dict = {'attendance_date':i['attendance_date'],'check_in':i['in_time'],'check_out':i['out_time'],'status':status,'worked_hours':i['worked_hours']}
                attend_list.append(emp_dict)

            site_ids = models.execute_kw(db, uid, password,
            'site.master', 'search',
            [[]],)   
            site_detail = models.execute_kw(db, uid, password,
            'site.master', 'read',
            [site_ids],{'fields': ['name']})

            demp_ids = models.execute_kw(db, uid, password,
            'hr.department', 'search',
            [[]],)

            demp_detail = models.execute_kw(db, uid, password,
            'hr.department', 'read',
            [demp_ids],{'fields': ['name']})
            last = last_day_of_month(today1)
            print(last)
            print(today_atte,days)
            context = {'image':img_list,'emp':emp_detail,'today_atte':today_atte_data,'days':days,'firstday':first,'lastday':last,'attendance':attend_list,
            'present':present,'absent':absent,'half_day':half_day,'emp_name':emp_name,'child_list':child_list,'demp':demp_detail,'site':site_detail}
            # print(context)
            return render(request,'hr_search_attendance.html',context)
        else :
            return  HttpResponse('PLease select valid field')


    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))



def save_holidays(request):
    try:
        if request.method == "POST":
            holiday_name = request.POST.get('holidays_name')
            holidays_date = request.POST.get('holidays_date')
            holidays_active = request.POST.get('holidays_active')
            print(holidays_active)
            date = datetime.strptime(holidays_date,'%Y-%m-%d')
            print(date,type(date))
            if holidays_active == 'on':
                active = True
            else:
                active = False
            id = models.execute_kw(db, uid, password, 'holiday.master', 'create', [{
            'name':holiday_name,'holiday_date':date,'active':active}])
            messages.info(request,'Holidays Info save successfully')

            return redirect('/master_page/')
    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))



def save_shift(request):
    try:
        if request.method == "POST":
            shift_in= request.POST.get('shift_in')
            shift_out = request.POST.get('shift_out')
            shift_name = request.POST.get('shift_name')
            id = models.execute_kw(db, uid, password, 'hr.employee.shift.timing', 'create', [{
            'name':shift_name,'in_time':shift_in,'out_time':shift_out}])
            messages.info(request, 'Shift Info save successfully')

            return redirect('/master_page/')

    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))


def save_state(request):
    try:
        if request.method == 'POST':
            state_name = request.POST.get('state_name')
            state_active = request.POST.get('state_active')
            union_territory = request.POST.get('union_territory')
            active = ''
            if state_active == 'on':
                active = True
            else:
                active = False
            union = ''
            if union_territory == 'on':
                union = True
            else:
                union = False

            id = models.execute_kw(db, uid, password, 'res.state', 'create', [{
            'name':state_name,'active':active,'union_territory':union}])
            messages.info(request,'State Info save successfully')

            return redirect('/master_page/')
    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))


def save_cost(request):
    try:
        if request.method == 'POST':
            # print(request.POST)
            Nominee_name = request.POST.get('Nominee_name')
            id = models.execute_kw(db, uid, password, 'cost.center', 'create', [{
            'name':Nominee_name}])
            messages.info(request,'Cost Center Info save successfully')

            return redirect('/master_page/')


    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))


def save_site(request):
    try:
        if request.method == 'POST':
            print(request.POST)
            site_name = request.POST.get('site_name')
            is_a_branch = request.POST.get('is_a_branch')
            flexishift = request.POST.get('flexishift')
            site_address = request.POST.get('site_address')
            branch = False
            if is_a_branch == 'on':
                branch = True
            
            shift = False
            if flexishift == 'on':
                shift = True

            id = models.execute_kw(db, uid, password, 'site.master', 'create', [{
            'name':site_name,'is_branch':branch,'flexishift':shift,'site_address':site_address}])
            messages.info(request,'Site Center Info save successfully')

            return redirect('/master_page/')

    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))


def save_site_location(request):
    try:
        if request.method == 'POST':
            print(request.POST)
            site_name = request.POST.get('site_location_name')
            state = request.POST.get('state_id')
            site_location_active = request.POST.get('site_location_active')

            active = False
            if site_location_active == 'on':
                active = True

            id = models.execute_kw(db, uid, password, 'res.city', 'create', [{
            'name':site_name,'state':int(state),'active':active}])
            messages.info(request,'Site Location Info save successfully')

            return redirect('/master_page/')
    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))


def save_designation(request):
    try:
        if request.method == 'POST':
            print(request.POST)
            designation_name = request.POST.get('designation_name')
            id = models.execute_kw(db, uid, password, 'hr.job', 'create', [{
            'name':designation_name}])
            messages.info(request,'Designation Info save successfully')
            return redirect('/master_page/')

    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))


def save_department(request):
    try:
        if request.method == 'POST':
            print(request.POST)
            Department_name = request.POST.get('Department_name')
            Department_active = request.POST.get('Department_active')

            active = False
            if Department_active == 'on':
                active = True

            id = models.execute_kw(db, uid, password, 'hr.department', 'create', [{
            'display_name':Department_name,'active':active,'name':Department_name}])
            messages.info(request,'Department_name Info save successfully')

            return redirect('/master_page/')
    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))

def upload_holidays(request):
    try:
        if request.method == "POST":
            try:
                holiday_csv = request.FILES["holiday_csv"]
                if not holiday_csv.name.endswith('.csv'):
                    messages.error(request,'File is not CSV type')
                    return HttpResponseRedirect(reverse('master_page'))
                if holiday_csv.multiple_chunks():
                    messages.error(request,"Uploaded file is too big (%.2f MB)." % (holiday_csv.size/(1000*1000),))
                    return HttpResponseRedirect(reverse("master_page"))
                
                file_data = holiday_csv.read().decode("utf-8")
                lines = file_data.split("\n")
                first = 0
                for line in lines:
                    if line != '':
                        if first != 0:
                            fields = line.split(',')
                            holiday_name = fields[0]
                            holiday_date = fields[1]
                            date = datetime.strptime(holiday_date,'%Y/%m/%d')
                            holiday_active = fields[2]
                            if holiday_active == '1' or holiday_active == True:
                                active = True
                            else:
                                active = False
                            id = models.execute_kw(db, uid, password, 'holiday.master', 'create', [{
                            'name':holiday_name,'holiday_date':date,'active':active}])
                            messages.info(request,'Holidays Info save successfully')
                    first+=1
                return redirect('/master_page/')
            except Exception as e:
                print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))
                logging.getLogger("error_logger").error("Unable to upload file. "+repr(e))
                messages.error(request,"Unable to upload file. "+repr(e))
                return HttpResponseRedirect(reverse("master_page"))
    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))


def upload_department(request):
    try:
        if request.method == "POST":
            print(request.FILES)
            try:
                department_csv = request.FILES["department_csv"]
                print(department_csv)
                if not department_csv.name.endswith('.csv'):
                    messages.error(request,'File is not CSV type')
                    return HttpResponseRedirect(reverse('master_page'))
                if department_csv.multiple_chunks():
                    messages.error(request,"Uploaded file is too big (%.2f MB)." % (holiday_csv.size/(1000*1000),))
                    return HttpResponseRedirect(reverse("master_page"))
                file_data = department_csv.read().decode("utf-8")
                lines = file_data.split("\n")
                first = 0
                for line in lines:
                    if line != '':
                        if first != 0:
                            fields = line.split(',')
                            Department_name = fields[0]
                            Department_active = fields[1]
                            print(Department_name)
                            if Department_active == '1' or holiday_active == True:
                                active = True
                            else:
                                active = False
                            id = models.execute_kw(db, uid, password, 'hr.department', 'create', [{
                            'display_name':Department_name,'active':active,'name':Department_name}])
                            messages.info(request,'Department_name Info save successfully')
                    first+=1
                return redirect('/master_page/')
            except Exception as e:
                print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))
                logging.getLogger("error_logger").error("Unable to upload file. "+repr(e))
                messages.error(request,"Unable to upload file. "+repr(e))
                return HttpResponseRedirect(reverse("master_page"))
    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))



def upload_shift(request):
    try:
        if request.method == "POST":
            try:
                shift_csv = request.FILES["shift_csv"]
                if not shift_csv.name.endswith('.csv'):
                    messages.error(request,'File is not CSV type')
                    return HttpResponseRedirect(reverse('master_page'))
                if shift_csv.multiple_chunks():
                    messages.error(request,"Uploaded file is too big (%.2f MB)." % (holiday_csv.size/(1000*1000),))
                    return HttpResponseRedirect(reverse("master_page"))
                file_data = shift_csv.read().decode("utf-8")
                lines = file_data.split("\n")
                first = 0
                for line in lines:
                    if line != '':
                        if first != 0:
                            fields = line.split(',')
                            shift_name = fields[0]
                            shift_in = fields[1]
                            shift_out = fields[2]
                            id = models.execute_kw(db, uid, password, 'hr.employee.shift.timing', 'create', [{
                            'name':shift_name,'in_time':shift_in,'out_time':shift_out}])
                            messages.info(request, 'Shift Info save successfully')
                    first+=1
                return redirect('/master_page/')   
            except Exception as e:
                print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))
                logging.getLogger("error_logger").error("Unable to upload file. "+repr(e))
                messages.error(request,"Unable to upload file. "+repr(e))
                return HttpResponseRedirect(reverse("master_page"))
    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))


def upload_state(request):
    try:
        if request.method == "POST":
            try:
                state_csv = request.FILES["state_csv"]
                if not state_csv.name.endswith('.csv'):
                    messages.error(request,'File is not CSV type')
                    return HttpResponseRedirect(reverse('master_page'))
                if state_csv.multiple_chunks():
                    messages.error(request,"Uploaded file is too big (%.2f MB)." % (holiday_csv.size/(1000*1000),))
                    return HttpResponseRedirect(reverse("master_page"))
                file_data = state_csv.read().decode("utf-8")
                lines = file_data.split("\n")
                first = 0
                for line in lines:
                    if line != '':
                        if first != 0:
                            fields = line.split(',')
                            state_name = fields[0]
                            state_active = fields[1]
                            union_territory = fields[2]
                            if state_active == '1' or state_active == True:
                                active = True
                            else:
                                active = False
                            if union_territory == '1' or union_territory == True:
                                union = True
                            else:
                                union = False
                            id = models.execute_kw(db, uid, password, 'res.state', 'create', [{
                            'name':state_name,'active':active,'union_territory':union}])
                            messages.info(request,'State Info save successfully')
                    first+=1
                return redirect('/master_page/')   
            except Exception as e:
                print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))
                logging.getLogger("error_logger").error("Unable to upload file. "+repr(e))
                messages.error(request,"Unable to upload file. "+repr(e))
                return HttpResponseRedirect(reverse("master_page"))
    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))



def upload_designation(request):
    try:
        if request.method == "POST":
            try:
                designation_csv = request.FILES["designation_csv"]
                if not designation_csv.name.endswith('.csv'):
                    messages.error(request,'File is not CSV type')
                    return HttpResponseRedirect(reverse('master_page'))
                if designation_csv.multiple_chunks():
                    messages.error(request,"Uploaded file is too big (%.2f MB)." % (holiday_csv.size/(1000*1000),))
                    return HttpResponseRedirect(reverse("master_page"))
                file_data = designation_csv.read().decode("utf-8")
                lines = file_data.split("\n")
                first = 0
                for line in lines:
                    if line != '':
                        if first != 0:
                            fields = line.split(',')
                            designation_name = fields[0]
                            id = models.execute_kw(db, uid, password, 'hr.job', 'create', [{
                            'name':designation_name}])
                            messages.info(request,'Designation Info save successfully')
                    first+=1
                return redirect('/master_page/')   
            except Exception as e:
                print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))
                logging.getLogger("error_logger").error("Unable to upload file. "+repr(e))
                messages.error(request,"Unable to upload file. "+repr(e))
                return HttpResponseRedirect(reverse("master_page"))
    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))



def upload_cost(request):
    try:
        if request.method == "POST":
            try:
                cost_csv = request.FILES["cost_csv"]
                print(cost_csv)
                if not cost_csv.name.endswith('.csv'):
                    messages.error(request,'File is not CSV type')
                    return HttpResponseRedirect(reverse('master_page'))
                if cost_csv.multiple_chunks():
                    messages.error(request,"Uploaded file is too big (%.2f MB)." % (holiday_csv.size/(1000*1000),))
                    return HttpResponseRedirect(reverse("master_page"))
                file_data = cost_csv.read().decode("utf-8")
                lines = file_data.split("\n")
                print(lines)
                first = 0
                for line in lines:
                    if line != '':
                        if first != 0:
                            fields = line.split(',')
                            Nominee_name = fields[0]
                            id = models.execute_kw(db, uid, password, 'cost.center', 'create', [{
                            'name':Nominee_name}])
                            messages.info(request,'Cost Center Info save successfully')
                    first+=1
                return redirect('/master_page/')   
            except Exception as e:
                print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))
                logging.getLogger("error_logger").error("Unable to upload file. "+repr(e))
                messages.error(request,"Unable to upload file. "+repr(e))
                return HttpResponseRedirect(reverse("master_page"))
    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))

    


def upload_site(request):
    try:
        if request.method == "POST":
            print(request.FILES)
            try:
                site_csv = request.FILES["site_csv"]
                print(site_csv)
                if not site_csv.name.endswith('.csv'):
                    messages.error(request,'File is not CSV type')
                    return HttpResponseRedirect(reverse('master_page'))
                if site_csv.multiple_chunks():
                    return HttpResponseRedirect(reverse("master_page"))
                    messages.error(request,"Uploaded file is too big (%.2f MB)." % (site_csv.size/(1000*1000),))
                file_data = site_csv.read().decode("utf-8")
                lines = file_data.split("\n")
                first = 0
                for line in lines:
                    if line != '':
                        if first != 0:
                            fields = line.split(',')
                            site_name = fields[0]
                            site_address = fields[1]
                            id = models.execute_kw(db, uid, password, 'site.master', 'create', [{
                            'name':site_name,'site_address':site_address}])
                            messages.info(request,'Site Center Info save successfully')
                    first+=1
                return redirect('/master_page/')
            except Exception as e:
                print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))
                logging.getLogger("error_logger").error("Unable to upload file. "+repr(e))
                messages.error(request,"Unable to upload file. "+repr(e))
                return HttpResponseRedirect(reverse("master_page"))
    except Exception as e:
        print(e,'error of line number {}'.format(sys.exc_info()[-1].tb_lineno))






