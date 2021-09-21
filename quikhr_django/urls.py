"""quikhr_django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from frontend import views
from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    path('admin/', admin.site.urls),
    path('register/',views.register,name='register'),
    path('',views.user_login,name='login'),
    path('wallpost/',views.wallpost,name='wallpost'),
    path('employee_profile/',views.employee_profile,name='employee_profiel'),
    path('detail/<int:emp_code>/',views.employee_details,name='contact'),
    path('main_attendance/',views.attendance_base,name='attendance'),
    url(r'^logout/$', views.user_logout, name='logout'),
    path('team_attendance/',views.team_attendance,name='team_attendance'),
    path('create_wallpost/',views.create_wall_post,name='create_wallpost'),
    path('create_attendance_csv/',views.cron_create_attendance_csv,name='create_attendance_csv'),
    path('create_employee_profile/',views.create_employee,name='create_employee_profile'),
    path('user_profile/',views.user_profile,name='user_profile'),
    path('team_employee_profile/',views.team_employee_profile,name='team_employee_profile'),
    path('search/',views.search_function,name='search'),
    path('search_attendance/',views.search_attendance,name='search_attendance'),
    path('change_basic_details/',views.save_basic_info,name='change_basic_details'), 
    path('master_page/',views.master_table,name='master_page'),
    path('hr_attendance/',views.hr_attendance,name='hr_attendance'),
    path('hr_search_attendance/',views.hr_search_attendance,name='hr_search_attendance'),
    path('save_holidays/',views.save_holidays,name='save_holidays'),
    path('save_shift/',views.save_shift,name='save_shift'), 
    path('save_state/',views.save_state,name='save_state'),
    path('save_cost/',views.save_cost,name='save_cost'),
    path('save_site/',views.save_site,name='save_site'),
    path('save_site_location/',views.save_site_location,name='save_site_location'),
    path('save_designation/',views.save_designation,name='save_designation'),
    path('save_department/',views.save_department,name='save_department'),
    path('upload_holiday_csv/',views.upload_holidays,name='upload_holiday_csv'),
    path('upload_department_csv/',views.upload_department,name='upload_department'),
    path('upload_shift_csv/',views.upload_shift,name='upload_shift_csv'),
    path('upload_state_csv/',views.upload_state,name='upload_state_csv'),
    path('upload_designation_csv/',views.upload_designation,name='upload_designation_csv'),
    path('upload_cost_csv/',views.upload_cost,name='upload_cost_csv'),
    path('upload_site_csv/',views.upload_site,name='upload_site')

]+ static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
