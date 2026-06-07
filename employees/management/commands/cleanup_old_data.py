from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from employees.models import Attendance, ManualEntryPhoto, MonthlySalary, FaceCapture, LateAbsenceRecord
import os
from django.conf import settings
import json
from pathlib import Path


class Command(BaseCommand):
    help = "Self-cleaning: 2 oydan eski attendance, photo va maosh ma'lumotlarini avtomatik tozalaydi"

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=60,
            help='Necha kundan eski ma\'lumotlarni o\'chirish (default: 60)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Hech narsa o\'chirmay, faqat hisobot ko\'rsatish'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff = (timezone.now() - timedelta(days=days)).date()

        self.stdout.write(self.style.WARNING(f"\n{'='*60}"))
        self.stdout.write(self.style.WARNING(f"   SELF-CLEANING MODE"))
        self.stdout.write(self.style.WARNING(f"   {timezone.now().strftime('%d.%m.%Y %H:%M')}"))
        self.stdout.write(self.style.WARNING(f"   Chegara: {cutoff} ({days} kun)"))
        if dry_run:
            self.stdout.write(self.style.WARNING(f"   *** DRY RUN - HECH NARSA O'CHIRILMAYDI ***"))
        self.stdout.write(self.style.WARNING(f"{'='*60}\n"))

        total_deleted = 0
        report = {}

        # 1. Attendance (in)
        old_in = Attendance.objects.filter(date__lt=cutoff, type='in')
        cnt_in = old_in.count()
        report['attendance_in'] = cnt_in
        if not dry_run:
            old_in.delete()
        self.stdout.write(f"  Attendance (kelish): {cnt_in}")
        total_deleted += cnt_in

        # 2. Attendance (out)
        old_out = Attendance.objects.filter(date__lt=cutoff, type='out')
        cnt_out = old_out.count()
        report['attendance_out'] = cnt_out
        if not dry_run:
            old_out.delete()
        self.stdout.write(f"  Attendance (chiqish): {cnt_out}")
        total_deleted += cnt_out

        # 3. ManualEntryPhoto + fayllarni o'chirish
        old_photos = ManualEntryPhoto.objects.filter(captured_at__date__lt=cutoff)
        cnt_photos = old_photos.count()
        report['manual_photos'] = cnt_photos
        if not dry_run:
            for p in old_photos:
                if p.photo:
                    try:
                        fpath = os.path.join(settings.MEDIA_ROOT, p.photo.name)
                        if os.path.exists(fpath):
                            os.remove(fpath)
                    except Exception:
                        pass
            old_photos.delete()
        self.stdout.write(f"  ManualEntryPhoto: {cnt_photos}")
        total_deleted += cnt_photos

        # 4. MonthlySalary (2 oydan eski)
        old_salaries = MonthlySalary.objects.filter(
            year__lt=cutoff.year
        ) | MonthlySalary.objects.filter(
            year=cutoff.year, month__lt=cutoff.month
        )
        cnt_sal = old_salaries.count()
        report['monthly_salaries'] = cnt_sal
        if not dry_run:
            old_salaries.delete()
        self.stdout.write(f"  MonthlySalary: {cnt_sal}")
        total_deleted += cnt_sal

        # 5. FaceCapture + fayllarni o'chirish
        old_face_captures = FaceCapture.objects.filter(captured_at__date__lt=cutoff)
        cnt_face = old_face_captures.count()
        report['face_captures'] = cnt_face
        if not dry_run:
            for fc in old_face_captures:
                if fc.photo:
                    try:
                        fpath = os.path.join(settings.MEDIA_ROOT, fc.photo.name)
                        if os.path.exists(fpath):
                            os.remove(fpath)
                    except Exception:
                        pass
            old_face_captures.delete()
        self.stdout.write(f"  FaceCapture: {cnt_face}")
        total_deleted += cnt_face

        # 6. LateAbsenceRecord
        old_late_records = LateAbsenceRecord.objects.filter(date__lt=cutoff)
        cnt_late = old_late_records.count()
        report['late_absence_records'] = cnt_late
        if not dry_run:
            old_late_records.delete()
        self.stdout.write(f"  LateAbsenceRecord: {cnt_late}")
        total_deleted += cnt_late

        # 7. Attendance face_photo fayllarini tozalash
        old_att_faces = Attendance.objects.filter(date__lt=cutoff).exclude(face_photo='')
        cnt_att_faces = old_att_faces.count()
        report['attendance_face_photos'] = cnt_att_faces
        if not dry_run:
            for att in old_att_faces:
                if att.face_photo:
                    try:
                        fpath = os.path.join(settings.MEDIA_ROOT, att.face_photo.name)
                        if os.path.exists(fpath):
                            os.remove(fpath)
                        att.face_photo.delete(save=False)
                    except Exception:
                        pass
        self.stdout.write(f"  Attendance face photos: {cnt_att_faces}")
        total_deleted += cnt_att_faces

        # 8. Cleanup log fayli
        log_dir = Path(settings.BASE_DIR) / 'cleanup_logs'
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"cleanup_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'cutoff_date': str(cutoff),
            'days_threshold': days,
            'dry_run': dry_run,
            'deleted': report,
            'total_deleted': total_deleted
        }
        if not dry_run:
            log_file.write_text(json.dumps(log_data, indent=2, ensure_ascii=False))
            # Eski loglarni tozalash (30 dan ko'p bo'lsa)
            all_logs = sorted(log_dir.glob('*.json'), reverse=True)
            for old_log in all_logs[30:]:
                old_log.unlink()

        self.stdout.write(self.style.SUCCESS(f"\n  Jami o'chirilgan: {total_deleted}"))
        if dry_run:
            self.stdout.write(self.style.WARNING("  DRY RUN - hech narsa o'chirilmadi"))
        self.stdout.write(self.style.SUCCESS("  Self-cleaning tugadi!"))
        self.stdout.write(self.style.WARNING(f"{'='*60}\n"))
