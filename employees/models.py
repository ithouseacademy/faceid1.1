from django.db import models
from django.utils import timezone
from datetime import datetime, date, time, timedelta
import calendar
from django.db.models import Sum
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
# models.py ga qo'shing

class ManualEntryPhoto(models.Model):
    """Qo'lda kiritilgan xodimlarning yuz rasmlari"""

    ATTENDANCE_TYPES = [
        ('in', 'Kelish'),
        ('out', 'Chiqish'),
    ]

    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='manual_photos')
    photo = models.ImageField(upload_to='manual_entries/%Y/%m/%d/')
    attendance_type = models.CharField(max_length=3, choices=ATTENDANCE_TYPES, default='in', verbose_name='Tur')
    captured_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-captured_at']
        verbose_name = "Qo'lda kiritilgan rasm"
        verbose_name_plural = "Qo'lda kiritilgan rasmlar"

    def __str__(self):
        type_text = "Kelish" if self.attendance_type == 'in' else "Chiqish"
        return f"{self.employee} - {type_text} - {self.captured_at}"

    @property
    def type_display(self):
        return "Kelish" if self.attendance_type == 'in' else "Chiqish"




class UserProfile(models.Model):
    """Foydalanuvchi profili"""
    USER_TYPES = [
        ('admin', 'Administrator'),
        ('hr', 'HR Manager'),
        ('manager', 'Department Manager'),
        ('employee', 'Employee'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='employee')
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    employee = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='user_profile')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Foydalanuvchi profili'
        verbose_name_plural = 'Foydalanuvchi profillari'

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Har yangi user yaratilganda avtomatik profile yaratish"""
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """User saqlanganda profile ni saqlash"""
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)


class Employee(models.Model):
    WORK_DAYS_CHOICES = [
        ('monday', 'Dushanba'),
        ('tuesday', 'Seshanba'),
        ('wednesday', 'Chorshanba'),
        ('thursday', 'Payshanba'),
        ('friday', 'Juma'),
        ('saturday', 'Shanba'),
        ('sunday', 'Yakshanba'),
    ]

    first_name = models.CharField(max_length=100, verbose_name='Ismi')
    last_name = models.CharField(max_length=100, verbose_name='Familyasi')
    position = models.CharField(max_length=100, verbose_name='Lavozimi')
    department = models.CharField(max_length=100, verbose_name="Bo'lim")
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefon')
    email = models.EmailField(blank=True, verbose_name='Email')
    photo = models.ImageField(upload_to='employee_photos/', verbose_name='Rasm')

    # Ish kunlari (masalan: ['monday', 'tuesday', ...])
    work_days = models.JSONField(default=list, verbose_name='Ish kunlari')

    # Har bir kun uchun ish jadvali
    # {"monday": {"start": "09:00", "end": "18:00"}, ...}
    work_schedule = models.JSONField(default=dict, verbose_name='Ish jadvali')

    monthly_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Oylik maosh'
    )

    late_penalty_per_minute = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1000,
        verbose_name='Har daqiqa uchun jarima'
    )

    allowed_late_minutes = models.IntegerField(
        default=10,
        verbose_name='Ruxsat etilgan kechikish (daq.)'
    )

    daily_work_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=8.0,
        verbose_name='Kunlik ish soatlari'
    )

    is_active = models.BooleanField(default=True, verbose_name='Faol')
    cache_version = models.IntegerField(default=0, verbose_name='Kesh versiyasi')
    notes = models.TextField(blank=True, verbose_name='Izoh')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')

    class Meta:
        ordering = ['first_name', 'last_name']
        verbose_name = 'Xodim'
        verbose_name_plural = 'Xodimlar'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def work_days_display(self):
        day_mapping = dict(self.WORK_DAYS_CHOICES)
        return ", ".join([day_mapping.get(day, day) for day in self.work_days])

    @property
    def get_image_url(self):
        if self.photo:
            return self.photo.url
        return None

    def get_daily_schedule(self, day_code):
        schedule = self.work_schedule.get(day_code, {})
        return {
            'start': schedule.get('start', '09:00'),
            'end': schedule.get('end', '18:00'),
            'is_work_day': day_code in self.work_days
        }

    def get_today_schedule(self):
        today_code = datetime.now().strftime('%A').lower()
        return self.get_daily_schedule(today_code)

    def calculate_daily_salary(self, year=None, month=None):
        if not self.monthly_salary or not self.work_days:
            return 0

        if not year or not month:
            today = date.today()
            year = today.year
            month = today.month

        days_in_month = calendar.monthrange(year, month)[1]
        work_days_count = 0

        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            if current_date.strftime('%A').lower() in self.work_days:
                work_days_count += 1

        if work_days_count == 0:
            return 0

        return self.monthly_salary / work_days_count

    def check_late_penalty(self, check_in_time, check_date=None):
        if not check_in_time:
            return 0

        if check_date is None:
            check_date = date.today()

        day_code = check_date.strftime('%A').lower()
        schedule = self.get_daily_schedule(day_code)

        if not schedule['is_work_day']:
            return 0

        scheduled_time = datetime.strptime(schedule['start'], '%H:%M').time()
        scheduled_dt = datetime.combine(check_date, scheduled_time)
        actual_dt = datetime.combine(check_date, check_in_time)

        if actual_dt > scheduled_dt:
            late_minutes_total = (actual_dt - scheduled_dt).seconds // 60
            effective_late_minutes = max(0, late_minutes_total - self.allowed_late_minutes)
            return effective_late_minutes * self.late_penalty_per_minute

        return 0

    def get_total_penalty(self, year=None, month=None):
        """Calculate total penalty for a specific month"""
        if year is None or month is None:
            today = date.today()
            year = today.year
            month = today.month

        try:
            # Get all late attendance records for this month
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)

            # Calculate total penalty from attendance records
            total_penalty = Attendance.objects.filter(
                employee=self,
                date__gte=start_date,
                date__lt=end_date,
                type='in',
                status='late'
            ).aggregate(total=Sum('penalty_amount'))['total'] or 0

            return total_penalty
        except Exception as e:
            print(f"Error calculating penalty for {self.full_name}: {e}")
            return 0

    def get_monthly_penalty(self):
        """Get penalty for current month"""
        return self.get_total_penalty()

    def get_today_penalty(self):
        """Get penalty for today"""
        today = date.today()
        today_attendance = Attendance.objects.filter(
            employee=self,
            date=today,
            type='in',
            status='late'
        ).first()

        if today_attendance:
            return today_attendance.penalty_amount
        return 0

    def get_current_month_penalty_details(self):
        """Get detailed penalty info for current month"""
        today = date.today()
        year = today.year
        month = today.month

        return self.get_month_penalty_details(year, month)

    def get_month_penalty_details(self, year, month):
        """Get detailed penalty info for specific month"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        # Get all late attendances for the month
        late_attendances = Attendance.objects.filter(
            employee=self,
            date__gte=start_date,
            date__lt=end_date,
            type='in',
            status='late'
        ).order_by('-date')

        # Calculate totals
        total_penalty = late_attendances.aggregate(total=Sum('penalty_amount'))['total'] or 0
        total_late_minutes = late_attendances.aggregate(total=Sum('late_minutes'))['total'] or 0
        late_days = late_attendances.count()

        # Get daily penalties
        daily_penalties = []
        for attendance in late_attendances:
            daily_penalties.append({
                'date': attendance.date,
                'time': attendance.time,
                'late_minutes': attendance.late_minutes,
                'penalty_amount': attendance.penalty_amount
            })

        return {
            'total_penalty': total_penalty,
            'total_late_minutes': total_late_minutes,
            'late_days': late_days,
            'daily_penalties': daily_penalties,
            'month': month,
            'year': year,
            'month_name': self.get_month_name(month)
        }

    def get_monthly_penalty_history(self, limit=6):
        """Get penalty history for last few months"""
        penalties = []
        today = date.today()

        for i in range(limit):
            month = today.month - i
            year = today.year

            if month <= 0:
                month += 12
                year -= 1

            penalty_details = self.get_month_penalty_details(year, month)
            penalties.append(penalty_details)

        return penalties

    def get_month_name(self, month):
        months = [
            'Yanvar', 'Fevral', 'Mart', 'Aprel',
            'May', 'Iyun', 'Iyul', 'Avgust',
            'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr'
        ]
        return months[month-1] if 1 <= month <= 12 else ''

    def get_late_days_count(self, year, month):
        """Get number of late days for specific month"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        return Attendance.objects.filter(
            employee=self,
            date__gte=start_date,
            date__lt=end_date,
            type='in',
            status='late'
        ).count()

    def get_total_late_minutes(self, year, month):
        """Get total late minutes for specific month"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        total = Attendance.objects.filter(
            employee=self,
            date__gte=start_date,
            date__lt=end_date,
            type='in',
            status='late'
        ).aggregate(total=Sum('late_minutes'))['total']

        return total or 0

    def get_work_days_count(self, year, month):
        """Get number of work days for specific month"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        work_days_count = 0
        current_date = start_date

        while current_date < end_date:
            day_code = current_date.strftime('%A').lower()
            if day_code in self.work_days:
                work_days_count += 1
            current_date += timedelta(days=1)

        return work_days_count

    def get_present_days_count(self, year, month):
        """Get number of present days for specific month (only work days)"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        # Get all attendances
        attendances = Attendance.objects.filter(
            employee=self,
            date__gte=start_date,
            date__lt=end_date,
            type='in'
        )

        # Count only work days where status is not 'day_off'
        present_count = 0
        for attendance in attendances:
            day_code = attendance.date.strftime('%A').lower()
            if day_code in self.work_days and attendance.status != 'day_off':
                present_count += 1

        return present_count

    def get_day_off_days_count(self, year, month):
        """Get number of day_off attendances (non-work days or work days marked as day_off)"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        # Count attendances where status is 'day_off'
        day_off_count = Attendance.objects.filter(
            employee=self,
            date__gte=start_date,
            date__lt=end_date,
            type='in',
            status='day_off'
        ).count()

        return day_off_count


class Attendance(models.Model):
    ATTENDANCE_TYPES = [
        ('in', 'Kelish'),
        ('out', 'Chiqish'),
    ]

    STATUS_CHOICES = [
        ('ontime', 'Vaqtida'),
        ('late', 'Kechikdi'),
        ('early', 'Erta keldi'),
        ('absent', "Kelmagan"),
        ('day_off', 'Dam olish kuni'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    time = models.TimeField()
    type = models.CharField(max_length=3, choices=ATTENDANCE_TYPES, default='in')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ontime')
    late_minutes = models.IntegerField(default=0)
    penalty_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    face_photo = models.ImageField(upload_to='attendance_faces/%Y/%m/%d/', null=True, blank=True, verbose_name='Yuz rasmi')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time']
        unique_together = ['employee', 'date', 'type']
        verbose_name = 'Davomat'
        verbose_name_plural = 'Davomatlar'

    def __str__(self):
        type_text = "Kelish" if self.type == 'in' else "Chiqish"
        return f"{self.employee.full_name} - {self.date} {self.time} ({type_text})"

    @property
    def type_display(self):
        return "Kelish" if self.type == 'in' else "Chiqish"

    @property
    def is_work_day(self):
        """Check if this attendance was on a work day"""
        day_code = self.date.strftime('%A').lower()
        return day_code in self.employee.work_days

    def calculate_late_status(self):
        """Dam olish kunlarini to'g'ri hisoblash"""
        if self.type != 'in' or not self.time:
            return self.status

        check_date = self.date
        check_in_time = self.time

        day_code = check_date.strftime('%A').lower()
        schedule = self.employee.get_daily_schedule(day_code)

        # **ASOSIY O'ZGARISH: Ish kuni EMAS bo'lsa, day_off qilib belgilash**
        if not schedule['is_work_day']:
            self.status = 'day_off'
            self.late_minutes = 0
            self.penalty_amount = 0
            self.save()
            return self.status

        # Ish kuni bo'lsa, oddiy hisoblash
        scheduled_time = datetime.strptime(schedule['start'], '%H:%M').time()
        scheduled_dt = datetime.combine(check_date, scheduled_time)
        actual_dt = datetime.combine(check_date, check_in_time)

        if actual_dt > scheduled_dt:
            late_minutes_total = (actual_dt - scheduled_dt).seconds // 60
            self.late_minutes = max(0, late_minutes_total - self.employee.allowed_late_minutes)

            if self.late_minutes > 0:
                self.status = 'late'
                self.penalty_amount = self.late_minutes * self.employee.late_penalty_per_minute
            else:
                self.status = 'ontime'
                self.penalty_amount = 0
        elif actual_dt < scheduled_dt:
            self.status = 'early'
            self.late_minutes = 0
            self.penalty_amount = 0
        else:
            self.status = 'ontime'
            self.late_minutes = 0
            self.penalty_amount = 0

        self.save()
        return self.status


class MonthlySalary(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salaries')
    year = models.IntegerField()
    month = models.IntegerField()

    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_penalty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    work_days = models.IntegerField(default=0)
    present_days = models.IntegerField(default=0)
    late_days = models.IntegerField(default=0)
    absent_days = models.IntegerField(default=0)
    day_off_days = models.IntegerField(default=0)
    total_late_minutes = models.IntegerField(default=0)

    notes = models.TextField(blank=True)
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', '-month']
        unique_together = ['employee', 'year', 'month']
        verbose_name = 'Oylik maosh'
        verbose_name_plural = 'Oylik maoshlar'

    def __str__(self):
        month_names = [
            '', 'Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun',
            'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr'
        ]
        return f"{self.employee.full_name} - {month_names[self.month]} {self.year}"

    def get_month_display(self):
        month_names = {
            1: 'Yanvar', 2: 'Fevral', 3: 'Mart', 4: 'Aprel',
            5: 'May', 6: 'Iyun', 7: 'Iyul', 8: 'Avgust',
            9: 'Sentabr', 10: 'Oktabr', 11: 'Noyabr', 12: 'Dekabr'
        }
        return month_names.get(self.month, str(self.month))

    def calculate_salary(self):
        """
        Sof maoshni to'g'ri hisoblash:
        Dam olish kunlarida kelganlar ish kuni deb hisoblanmaydi!
        """
        try:
            # 1. ASOSIY MAOSH
            self.basic_salary = self.employee.monthly_salary or 0

            # 2. OY ORALIG'I
            start_date = date(self.year, self.month, 1)
            if self.month == 12:
                end_date = date(self.year + 1, 1, 1)
            else:
                end_date = date(self.year, self.month + 1, 1)

            # 3. DAVOMATLARNI OLISH
            attendances = Attendance.objects.filter(
                employee=self.employee,
                date__gte=start_date,
                date__lt=end_date,
                type='in'
            ).order_by('date')

            # 4. ISH KUNLARI SONI
            self.work_days = 0
            work_dates = []
            current_date = start_date
            while current_date < end_date:
                day_code = current_date.strftime('%A').lower()
                if day_code in self.employee.work_days:
                    self.work_days += 1
                    work_dates.append(current_date)
                current_date += timedelta(days=1)

            # 5. KELGAN KUNLARNI TO'G'RI HISOBLASH
            work_day_attendance_dates = []
            day_off_attendance_dates = []

            for attendance in attendances:
                day_code = attendance.date.strftime('%A').lower()
                schedule = self.employee.get_daily_schedule(day_code)

                if schedule['is_work_day']:
                    # ISH KUNI: faqat status 'day_off' bo'lmaganlar ish kuni deb hisoblanadi
                    if attendance.status != 'day_off':
                        # Bitta kunga bir marta kelishni hisoblaymiz
                        if attendance.date not in work_day_attendance_dates:
                            work_day_attendance_dates.append(attendance.date)
                    else:
                        # Ish kuni bo'lsa ham, agar day_off deb belgilangan bo'lsa
                        if attendance.date not in day_off_attendance_dates:
                            day_off_attendance_dates.append(attendance.date)
                else:
                    # DAM OLISH KUNI: hamma holatda day_off
                    if attendance.date not in day_off_attendance_dates:
                        day_off_attendance_dates.append(attendance.date)

            # 6. STATISTIKALARNI SAQLASH
            self.present_days = len(work_day_attendance_dates)
            self.day_off_days = len(day_off_attendance_dates)

            # 7. KECHIKISH KUNLARI
            self.late_days = attendances.filter(
                date__in=work_day_attendance_dates,
                status='late'
            ).count()

            # 8. UMUMIY KECHIKISH DAQIQALARI
            late_attendances = attendances.filter(
                date__in=work_day_attendance_dates,
                status='late'
            )
            self.total_late_minutes = late_attendances.aggregate(total=Sum('late_minutes'))['total'] or 0

            # 9. KELMAGAN KUNLAR
            self.absent_days = max(0, self.work_days - self.present_days)

            # 10. JARIMALARNI HISOBLASH
            # a) Kechikish jarimalari
            late_penalty = attendances.filter(
                date__in=work_day_attendance_dates,
                status='late'
            ).aggregate(total=Sum('penalty_amount'))['total'] or 0

            # b) Kunlik maoshni hisoblash
            if self.work_days > 0:
                daily_salary = self.basic_salary / self.work_days
            else:
                daily_salary = 0

            # c) Kelmaganlik jarimasi
            absent_penalty = self.absent_days * daily_salary

            # d) Jami jarima
            self.total_penalty = late_penalty + absent_penalty

            # 11. SOF MAOSHNI HISOBLASH
            # Sof maosh = Asosiy maosh - Jami jarima + Mukofotlar
            self.net_salary = self.basic_salary - self.total_penalty + self.total_bonus

            # Sof maosh manfiy bo'lmasligi kerak
            if self.net_salary < 0:
                self.net_salary = 0

            # 12. SAQLASH
            self.save()

            return self.net_salary

        except Exception as e:
            print(f"XATO: Maosh hisoblashda xatolik - {str(e)}")
            # Agar xato bo'lsa, standart qiymatlarni qo'yamiz
            self.basic_salary = self.employee.monthly_salary or 0
            self.total_penalty = 0
            self.net_salary = self.basic_salary
            self.save()
            return self.net_salary


class Location(models.Model):
    name = models.CharField(max_length=200, verbose_name='Lokatsiya nomi')
    building = models.CharField(max_length=200, verbose_name='Bino nomi')
    address = models.TextField(verbose_name='Manzil')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Kenglik (Latitude)')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Uzunlik (Longitude)')
    radius_meters = models.PositiveIntegerField(default=100, verbose_name='Face ID masofasi (metr)')
    branch_name = models.CharField(max_length=200, blank=True, verbose_name='Filial/Bino nomi')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Lokatsiya'
        verbose_name_plural = 'Lokatsiyalar'

    def __str__(self):
        return f"{self.name} - {self.building}"


class FaceCapture(models.Model):
    ATTENDANCE_TYPES = [
        ('in', 'Kelish'),
        ('out', 'Chiqish'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='face_captures', verbose_name='Xodim')
    attendance = models.ForeignKey(Attendance, on_delete=models.SET_NULL, null=True, blank=True, related_name='face_captures', verbose_name='Davomat')
    photo = models.ImageField(upload_to='face_captures/%Y/%m/%d/', verbose_name='Rasm')
    attendance_type = models.CharField(max_length=3, choices=ATTENDANCE_TYPES, verbose_name='Tur')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='face_captures', verbose_name='Lokatsiya')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    captured_at = models.DateTimeField(auto_now_add=True, verbose_name='Olingan vaqt')

    class Meta:
        ordering = ['-captured_at']
        verbose_name = 'Face ID rasm'
        verbose_name_plural = 'Face ID rasmlar'

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_attendance_type_display()} - {self.captured_at}"

    @property
    def type_display(self):
        return "Kelish" if self.attendance_type == 'in' else 'Chiqish'


class LateAbsenceRecord(models.Model):
    RECORD_TYPES = [
        ('late', 'Kechikish'),
        ('absent', 'Kelmagan'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='late_absence_records', verbose_name='Xodim')
    record_type = models.CharField(max_length=10, choices=RECORD_TYPES, verbose_name='Tur')
    date = models.DateField(verbose_name='Sana')
    late_minutes = models.PositiveIntegerField(default=0, verbose_name='Kechikish (daq.)')
    reason = models.TextField(blank=True, verbose_name='Sabab')
    admin_note = models.TextField(blank=True, verbose_name='Admin izohi')
    attendance = models.ForeignKey(Attendance, on_delete=models.SET_NULL, null=True, blank=True, related_name='late_absence_records', verbose_name='Davomat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['employee', 'date', 'record_type']
        verbose_name = 'Kechikish/Kelmaganlik'
        verbose_name_plural = 'Kechikish/Kelmaganliklar'

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_record_type_display()} - {self.date}"


class CleanupConfig(models.Model):
    """Avtomatik tozalash sozlamalari"""
    auto_enabled = models.BooleanField(default=False, verbose_name='Avtomatik tozalash yoqilgan')
    months_back = models.PositiveIntegerField(default=2, verbose_name='Necha oydan eski ma\'lumotlar')
    interval_days = models.PositiveIntegerField(default=60, verbose_name='Oraliq (kun)')
    clean_face_captures = models.BooleanField(default=True, verbose_name='Face ID rasmlar')
    clean_attendance_photos = models.BooleanField(default=True, verbose_name='Davomat rasmlar')
    clean_attendance_records = models.BooleanField(default=True, verbose_name='Davomat yozuvlari')
    last_run = models.DateTimeField(null=True, blank=True, verbose_name='Oxirgi tozalash')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Avtomatik tozalash sozlamasi'
        verbose_name_plural = 'Avtomatik tozalash sozlamalari'

    def __str__(self):
        return f"Avtomatik tozalash: {'Yoqilgan' if self.auto_enabled else 'O\'chirilgan'}"