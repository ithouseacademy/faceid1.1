from django.contrib import admin
from .models import Employee, Attendance, MonthlySalary, ManualEntryPhoto, Location, FaceCapture, LateAbsenceRecord

@admin.register(ManualEntryPhoto)
class ManualEntryPhotoAdmin(admin.ModelAdmin):
    list_display = ['employee', 'captured_at', 'ip_address', 'photo_preview']
    list_filter = ['captured_at', 'employee']
    search_fields = ['employee__full_name', 'ip_address']
    readonly_fields = ['captured_at', 'ip_address', 'user_agent', 'photo_preview']
    
    def photo_preview(self, obj):
        if obj.photo:
            return f'<img src="{obj.photo.url}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />'
        return '-'
    photo_preview.allow_tags = True
    photo_preview.short_description = "Rasm"




    
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position', 'department', 'monthly_salary', 'is_active')
    list_filter = ('department', 'is_active', 'position')
    search_fields = ('first_name', 'last_name', 'position', 'department')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Shaxsiy ma\'lumotlar', {
            'fields': ('first_name', 'last_name', 'photo')
        }),
        ('Ish ma\'lumotlari', {
            'fields': ('position', 'department', 'monthly_salary')
        }),
        ('Ish jadvali', {
            'fields': ('work_days', 'work_schedule', 'daily_work_hours')
        }),
        ('Jarimalar', {
            'fields': ('late_penalty_per_minute', 'allowed_late_minutes')
        }),
        ('Aloqa', {
            'fields': ('phone', 'email')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
        }),
    )

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'time', 'type_display', 'status', 'late_minutes', 'penalty_amount')
    list_filter = ('date', 'type', 'status', 'employee__department')
    search_fields = ('employee__first_name', 'employee__last_name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'date'

@admin.register(MonthlySalary)
class MonthlySalaryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'year', 'month', 'net_salary', 'total_penalty', 'is_paid')
    list_filter = ('year', 'month', 'is_paid', 'employee__department')
    search_fields = ('employee__first_name', 'employee__last_name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'address', 'radius_meters', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'building', 'address')

@admin.register(FaceCapture)
class FaceCaptureAdmin(admin.ModelAdmin):
    list_display = ('employee', 'attendance_type', 'captured_at', 'location')
    list_filter = ('attendance_type', 'captured_at', 'location')
    search_fields = ('employee__first_name', 'employee__last_name')
    readonly_fields = ('captured_at',)

@admin.register(LateAbsenceRecord)
class LateAbsenceRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'record_type', 'date', 'late_minutes', 'reason')
    list_filter = ('record_type', 'date', 'employee__department')
    search_fields = ('employee__first_name', 'employee__last_name')