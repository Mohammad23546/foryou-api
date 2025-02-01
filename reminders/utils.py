from rest_framework.decorators import api_view
from rest_framework.response import Response
import re
from datetime import datetime, timedelta

def analyze_spoken_time(spoken_text):
    # قاموس للكلمات العربية المتعلقة بالوقت
    time_patterns = {
        # الفصحى
        'صباحا': 'AM', 'صباحاً': 'AM',
        'مساء': 'PM', 'مساءً': 'PM',
        'ظهرا': 'PM', 'ظهراً': 'PM',
        'عصرا': 'PM', 'عصراً': 'PM',
        'ليلا': 'PM', 'ليلاً': 'PM',
        'فجرا': 'AM', 'فجراً': 'AM',
        
        # اللهجة المصرية
        'الصبح': 'AM', 'بدري': 'AM',
        'بليل': 'PM', 'بالليل': 'PM',
        'العصر': 'PM', 'الضهر': 'PM',
        'بالنهار': 'AM', 'الفجر': 'AM',
        'بعد الضهر': 'PM', 'آخر الليل': 'AM',
        
        # اللهجة الخليجية
        'الفير': 'AM', 'الفجر': 'AM',
        'الصبح': 'AM', 'العصر': 'PM',
        'المغرب': 'PM', 'العشا': 'PM',
        'الضحى': 'AM', 'الظهر': 'PM',
        'باجر': 'AM', 'الشروق': 'AM',
        'عقب الظهر': 'PM', 'قبل الظهر': 'AM',
        
        # اللهجة الشامية
        'بكير': 'AM', 'الصبحية': 'AM',
        'بالعشي': 'PM', 'بالمسا': 'PM',
        'بالعتمة': 'PM', 'بالضحى': 'AM',
        'بالليل': 'PM', 'بالنهار': 'AM',
        
        # اللهجة العراقية
        'الصبح': 'AM', 'بالصبح': 'AM',
        'العصر': 'PM', 'بالعصر': 'PM',
        'الليل': 'PM', 'بالليل': 'PM',
        'نص الليل': 'AM', 'بالفجر': 'AM',
        
        # اللهجة المغربية
        'الصباح': 'AM', 'فالصباح': 'AM',
        'العشية': 'PM', 'فالعشية': 'PM',
        'الليل': 'PM', 'فالليل': 'PM',
        'الفجر': 'AM', 'الصبيحة': 'AM',
        
        # اللهجة السودانية
        'الصباح': 'AM', 'بكرة': 'AM',
        'العصرية': 'PM', 'الليل': 'PM',
        'نص الليل': 'AM', 'الفجرية': 'AM',
    }

    # قاموس للأرقام المكتوبة بالعربية
    arabic_numbers = {
        # الفصحى
        'واحد': 1, 'واحدة': 1,
        'اثنين': 2, 'اثنان': 2,
        'ثلاث': 3, 'ثلاثة': 3,
        'أربع': 4, 'أربعة': 4,
        'خمس': 5, 'خمسة': 5,
        'ست': 6, 'ستة': 6,
        'سبع': 7, 'سبعة': 7,
        'ثمان': 8, 'ثمانية': 8,
        'تسع': 9, 'تسعة': 9,
        'عشر': 10, 'عشرة': 10,
        'إحدى عشر': 11, 'احدى عشر': 11,
        'اثنى عشر': 12, 'اثني عشر': 12,
        
        # اللهجة المصرية
        'وحدة': 1, 'واحد': 1,
        'اتنين': 2, 'تنين': 2,
        'تلاتة': 3, 'تلات': 3,
        'اربعة': 4, 'اربع': 4,
        'خمسة': 5, 'خمس': 5,
        'ستة': 6, 'ست': 6,
        'سبعة': 7, 'سبع': 7,
        'تمنية': 8, 'تمن': 8,
        'تسعة': 9, 'تسع': 9,
        'عشرة': 10, 'عشر': 10,
        'حداشر': 11, 'طناشر': 12,
        
        # اللهجة الخليجية
        'وحده': 1, 'واحد': 1,
        'ثنين': 2, 'اثنين': 2,
        'ثلاث': 3, 'ثلاثه': 3,
        'اربع': 4, 'اربعه': 4,
        'خمس': 5, 'خمسه': 5,
        'ست': 6, 'سته': 6,
        'سبع': 7, 'سبعه': 7,
        'ثمان': 8, 'ثمانيه': 8,
        'تسع': 9, 'تسعه': 9,
        'عشر': 10, 'عشره': 10,
        'حدعش': 11, 'ثنعش': 12,
        
        # اللهجة الشامية
        'وحدي': 1, 'تنتين': 2,
        'تلاتي': 3, 'أربعة': 4,
        'خمسي': 5, 'ستة': 6,
        'سبعة': 7, 'تماني': 8,
        'تسعة': 9, 'عشرة': 10,
        'حدعشر': 11, 'طنعشر': 12,
    }

    # قاموس للدقائق
    minute_patterns = {
        # الفصحى
        'ربع': 15, 'نص': 30,
        'نصف': 30, 'ثلث': 20,
        'ثلثين': 40,
        
        # اللهجات المختلفة
        'ونص': 30, 'وربع': 15,
        'الا ربع': -15, 'إلا ربع': -15,
        'وتلت': 20, 'وتلات': 20,
        'ونصف': 30, 'وثلث': 20,
        'غير ربع': -15, 'الا خمس': -5,
        'وخمس': 5, 'وعشر': 10,
        'الا عشر': -10, 'وتلث': 20,
        'الا تلت': -20, 'ودقيقة': 1,
        'الا دقيقة': -1, 'وربوع': 15,
        'الا ربوع': -15, 'ونصة': 30,
        'وخمسة': 5, 'وعشرة': 10,
        'الا خمسة': -5, 'الا عشرة': -10,
        'وتلاتة': 3, 'الا تلاتة': -3,
    }

    # English time patterns
    english_time_patterns = {
        'morning': 'AM',
        'afternoon': 'PM',
        'evening': 'PM',
        'night': 'PM',
        'midnight': 'AM',
        'noon': 'PM',
        'am': 'AM',
        'pm': 'PM',
        'a.m': 'AM',
        'p.m': 'PM',
        'a.m.': 'AM',
        'p.m.': 'PM',
        'dawn': 'AM',
        'sunrise': 'AM',
        'sunset': 'PM',
        'dusk': 'PM',
    }

    # English number words
    english_numbers = {
        'one': 1,
        'two': 2,
        'three': 3,
        'four': 4,
        'five': 5,
        'six': 6,
        'seven': 7,
        'eight': 8,
        'nine': 9,
        'ten': 10,
        'eleven': 11,
        'twelve': 12,
        'quarter': 15,
        'half': 30,
    }

    # English minute patterns
    english_minute_patterns = {
        'quarter': 15,
        'half': 30,
        'quarter past': 15,
        'quarter to': -15,
        'half past': 30,
        'minutes': 0,  # سيتم تحديد القيمة لاحقاً
        'minute': 0,   # سيتم تحديد القيمة لاحقاً
    }

    try:
        # تحويل النص إلى أحرف صغيرة للإنجليزية
        text_lower = spoken_text.lower()
        words = spoken_text.split()
        words_lower = text_lower.split()
        hour = 0
        minute = 0
        period = 'AM'  # افتراضي
        is_english = any(word in english_time_patterns or word in english_numbers for word in words_lower)

        if is_english:
            # English time processing
            for i, word in enumerate(words_lower):
                # Check for direct numbers
                if word.isdigit():
                    hour = int(word)
                # Check for written numbers
                elif word in english_numbers:
                    hour = english_numbers[word]
                
                # Check for special time patterns
                if word in english_time_patterns:
                    period = english_time_patterns[word]
                
                # Check for minute patterns
                if word in english_minute_patterns:
                    if word in ['minute', 'minutes']:
                        # Look for number before 'minutes'
                        if i > 0 and words_lower[i-1].isdigit():
                            minute = int(words_lower[i-1])
                    else:
                        minute = english_minute_patterns[word]
                
                # Handle "quarter/half past/to" patterns
                if word == 'past' and i > 0:
                    if words_lower[i-1] in ['quarter', 'half']:
                        minute = english_minute_patterns[words_lower[i-1]]
                elif word == 'to' and i > 0 and words_lower[i-1] == 'quarter':
                    minute = -15
                    if hour > 0:
                        hour -= 1

        else:
            # Arabic time processing (الكود العربي السابق)
            for word in words:
                # البحث عن الأرقام المباشرة (١،٢،٣)
                if re.match(r'[\u0660-\u0669]+', word):
                    hour = int(word.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')))
                    break
                # البحث عن الأرقام المكتوبة (واحد، اثنين)
                elif word in arabic_numbers:
                    hour = arabic_numbers[word]
                    break

            # البحث عن الدقائق
            for word in words:
                if word in minute_patterns:
                    minute = minute_patterns[word]
                    break
                elif 'و' in word and any(char.isdigit() for char in word):
                    try:
                        minute = int(re.findall(r'\d+', word)[0])
                    except:
                        pass

            # تحديد الفترة (صباحاً/مساءً)
            for word in words:
                if word in time_patterns:
                    period = time_patterns[word]
                    break

        # تعديل الساعة حسب الفترة
        if period == 'PM' and hour < 12:
            hour += 12
        elif period == 'AM' and hour == 12:
            hour = 0

        # Handle negative minutes (for "quarter to", "الا ربع", etc.)
        if minute < 0:
            minute = 60 + minute
            if hour > 0:
                hour -= 1
            else:
                hour = 23

        # تعديل الإخراج حسب اللغة
        if is_english:
            # English response
            period_str = period  # Keep AM/PM as is for English
            if hour == 0:
                hour_str = "twelve"
            elif hour == 12:
                hour_str = "twelve"
            else:
                hour_str = str(hour if hour <= 12 else hour - 12)

            # Format minutes for English
            if minute == 0:
                minute_str = "o'clock"
            elif minute == 15:
                minute_str = "quarter past"
            elif minute == 30:
                minute_str = "half past"
            elif minute == 45:
                minute_str = "quarter to"
                hour_str = str(hour + 1 if hour < 23 else 0)
            else:
                minute_str = str(minute) + " minutes"

            return Response({
                'hour': hour,
                'minute': minute,
                'period': period,
                'formatted_time': f"{hour_str} {minute_str} {period}",
                'isValid': True,
                'language': 'en'
            })
        else:
            # Arabic response
            return Response({
                'hour': hour,
                'minute': minute,
                'period': 'صباحاً' if period == 'AM' else 'مساءً',
                'formatted_time': f"الساعة {hour} و{minute} {'صباحاً' if period == 'AM' else 'مساءً'}",
                'isValid': True,
                'language': 'ar'
            })

    except Exception as e:
        # Error response based on detected language
        if is_english:
            return Response({
                'hour': 0,
                'minute': 0,
                'period': '',
                'formatted_time': '',
                'isValid': False,
                'error': str(e),
                'language': 'en'
            })
        else:
            return Response({
                'hour': 0,
                'minute': 0,
                'period': '',
                'formatted_time': '',
                'isValid': False,
                'error': str(e),
                'language': 'ar'
            }) 