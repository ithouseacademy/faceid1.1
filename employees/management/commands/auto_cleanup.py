from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from employees.models import Attendance, FaceCapture, CleanupConfig
from django.conf import settings
import os


class Command(BaseCommand):
    help = "CleanupConfig dagi sozlamalar bo'yicha avtomatik tozalash"

    def handle(self, *args, **options):
        config = CleanupConfig.objects.filter(pk=1).first()
        if not config or not config.auto_enabled:
            self.stdout.write("Avtomatik tozalash o'chirilgan")
            return

        now = timezone.now()
        if config.last_run and (now - config.last_run).days < config.interval_days:
            next_run = config.last_run + timedelta(days=config.interval_days)
            self.stdout.write(f"Hali vaqt emas. Keyingi tozalash: {next_run.strftime('%d.%m.%Y')}")
            return

        cutoff = now.date() - timedelta(days=config.months_back * 30)
        total = 0

        if config.clean_face_captures:
            qs = FaceCapture.objects.filter(captured_at__date__lt=cutoff)
            count = qs.count()
            for obj in qs:
                if obj.photo:
                    try:
                        fpath = os.path.join(settings.MEDIA_ROOT, obj.photo.name)
                        if os.path.exists(fpath):
                            os.remove(fpath)
                    except Exception:
                        pass
            qs.delete()
            self.stdout.write(f"  Face ID rasmlar: {count} ta o'chirildi")
            total += count

        if config.clean_attendance_photos:
            qs = Attendance.objects.exclude(face_photo='').filter(date__lt=cutoff)
            count = qs.count()
            for obj in qs:
                if obj.face_photo:
                    try:
                        fpath = os.path.join(settings.MEDIA_ROOT, obj.face_photo.name)
                        if os.path.exists(fpath):
                            os.remove(fpath)
                    except Exception:
                        pass
            qs.delete()
            self.stdout.write(f"  Davomat rasmlar: {count} ta o'chirildi")
            total += count

        if config.clean_attendance_records:
            qs = Attendance.objects.filter(date__lt=cutoff)
            count = qs.count()
            qs.delete()
            self.stdout.write(f"  Davomat yozuvlari: {count} ta o'chirildi")
            total += count

        config.last_run = now
        config.save()

        self.stdout.write(self.style.SUCCESS(f"Jami {total} ta ma'lumot o'chirildi"))
