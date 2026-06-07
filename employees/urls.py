# employees/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Asosiy sahifalar
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('save-manual-photo/', views.save_manual_entry_photo, name='save_manual_photo'),
    # urls.py ga qo'shing
   path('api/employee-photos/<int:employee_id>/', views.get_employee_photos_api, name='employee_photos_api'),
    # Dashboard va admin sahifalari
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Foydalanuvchi boshqaruvi
     path('users/', views.user_list, name='user_list'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('users/change-password/<int:user_id>/', views.change_user_password, name='change_user_password'),
    
    # Xodimlar boshqaruvi
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.add_employee, name='add_employee'),
    path('employees/edit/<int:id>/', views.edit_employee, name='edit_employee'),
    path('employees/delete/<int:id>/', views.delete_employee, name='delete_employee'),
    path('employees/<int:id>/', views.employee_detail, name='employee_detail'),
    
    # Face Recognition davomat
    path('checkin/', views.checkin_page, name='checkin'),
    path('checkout/', views.checkout_page, name='checkout'),
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
    
    # Hisobotlar
    path('reports/', views.attendance_report, name='reports'),
    path('daily-report/', views.daily_attendance_report, name='daily_report'),
    path('weekly-report/', views.weekly_attendance_report, name='weekly_report'),
    path('monthly-report/', views.monthly_attendance_report, name='monthly_report'),
    path('salary-report/', views.salary_report, name='salary_report'),
    path('export-monthly-excel/', views.export_monthly_excel, name='export_monthly_excel'),
    path('salaries/calculate/<int:employee_id>/<int:year>/<int:month>/', 
         views.calculate_monthly_salary, name='calculate_monthly_salary'),
    path('salaries/<int:salary_id>/mark-paid/', views.mark_salary_paid, name='mark_salary_paid'),
    
    # API'lar
    path('api/employee/<int:employee_id>/schedule/', views.get_employee_schedule, name='get_employee_schedule'),
    path('api/today-attendance/', views.get_today_attendance, name='get_today_attendance'),

    # Face Photo Gallery
    path('gallery/', views.face_gallery, name='gallery'),
    path('gallery/delete/<int:record_id>/', views.gallery_delete_photo, name='gallery_delete_photo'),

    # Location Management
    path('locations/', views.location_list, name='location_list'),
    path('locations/add/', views.location_add, name='location_add'),
    path('locations/edit/<int:id>/', views.location_edit, name='location_edit'),
    path('locations/delete/<int:id>/', views.location_delete, name='location_delete'),

    # Force Cache Refresh
    path('cache-refresh/', views.force_cache_refresh, name='force_cache_refresh'),

    # Late / Absence Monitoring
    path('monitoring/late/', views.late_monitoring, name='late_monitoring'),
    path('monitoring/late/<int:employee_id>/', views.late_monitoring_detail, name='late_monitoring_detail'),
    path('monitoring/record/edit/<int:record_id>/', views.late_record_edit, name='late_record_edit'),

    # Admin cleanup settings
    path('cleanup/', views.cleanup_settings, name='cleanup_settings'),
    path('cleanup/run/', views.run_cleanup, name='run_cleanup'),

    # Reports - PDF and Excel Export
    path('export-report-pdf/', views.export_report_pdf, name='export_report_pdf'),
    path('export-excel-report/', views.export_excel_report, name='export_excel_report'),

    # Old-style employee form (restored design)
    path('employees/add-old/', views.add_employee_old, name='add_employee_old'),
    path('employees/edit-old/<int:id>/', views.edit_employee_old, name='edit_employee_old'),

    # Password change (current user)
    path('password-change/', views.password_change_view, name='password_change'),
]
# urls.py
from django.views.generic import TemplateView

urlpatterns += [
    path(
        'service-worker.js',
        TemplateView.as_view(
            template_name='service-worker.js',
            content_type='application/javascript'
        ),
    ),
]
