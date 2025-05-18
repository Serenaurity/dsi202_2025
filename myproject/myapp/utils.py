# utils.py
from itertools import cycle

def distribute_training_days(days_per_week):
    """กระจายวันออกกำลังกายให้เหมาะสม"""
    if days_per_week >= 7:
        return list(range(1, 8))  # ทุกวัน
    
    # สร้างรูปแบบที่เหมาะสมสำหรับแต่ละจำนวนวัน
    if days_per_week == 1:
        return [1]  # วันจันทร์
    elif days_per_week == 2:
        return [1, 4]  # จันทร์, พฤหัสบดี
    elif days_per_week == 3:
        return [1, 3, 5]  # จันทร์, พุธ, ศุกร์
    elif days_per_week == 4:
        return [1, 3, 5, 7]  # จันทร์, พุธ, ศุกร์, อาทิตย์
    elif days_per_week == 5:
        return [1, 2, 4, 5, 7]  # จันทร์, อังคาร, พฤหัสบดี, ศุกร์, อาทิตย์
    elif days_per_week == 6:
        return [1, 2, 3, 5, 6, 7]  # ทุกวันยกเว้นพฤหัสบดี
    
    return list(range(1, days_per_week + 1))  # เริ่มจากวันจันทร์

def create_workout_exercises(workout_day, exercise_plan, primary_muscle=None):
    """สร้างรายการออกกำลังกายให้กับวันนั้นๆ"""
    from .models import Exercise, WorkoutExercise  # นำเข้าโมเดลที่เกี่ยวข้อง
    
    # ดึงท่าที่เหมาะสมตามระดับความสามารถ
    difficulty = exercise_plan.level
    
    # จำนวนท่าต่อวัน ขึ้นอยู่กับระดับความสามารถ
    if difficulty == 'beginner':
        exercises_per_day = 5
    elif difficulty == 'intermediate':
        exercises_per_day = 7
    else:  # advanced
        exercises_per_day = 9
    
    # จำนวนเซ็ตต่อท่า ขึ้นอยู่กับระดับความสามารถ
    if difficulty == 'beginner':
        sets = 3
        reps = "8-10"
        rest_time = 60
    elif difficulty == 'intermediate':
        sets = 4
        reps = "10-12"
        rest_time = 45
    else:  # advanced
        sets = 5
        reps = "8-12"
        rest_time = 30
    
    # ดึงท่าออกกำลังกายตามกล้ามเนื้อที่ต้องการเน้น
    if primary_muscle:
        # กรณี Push/Pull/Legs
        exercises = Exercise.objects.filter(
            muscle_group=primary_muscle,
            difficulty__in=[difficulty, 'beginner'] if difficulty != 'beginner' else ['beginner'],
            equipment_required=exercise_plan.available_equipment
        ).order_by('?')[:exercises_per_day]
    elif workout_day.focus == 'upper_body':
        # กรณีฝึกส่วนบน
        exercises = Exercise.objects.filter(
            muscle_group__in=['chest', 'back', 'shoulders', 'arms'],
            difficulty__in=[difficulty, 'beginner'] if difficulty != 'beginner' else ['beginner'],
            equipment_required=exercise_plan.available_equipment
        ).order_by('?')[:exercises_per_day]
    elif workout_day.focus == 'lower_body':
        # กรณีฝึกส่วนล่าง
        exercises = Exercise.objects.filter(
            muscle_group__in=['legs', 'core'],
            difficulty__in=[difficulty, 'beginner'] if difficulty != 'beginner' else ['beginner'],
            equipment_required=exercise_plan.available_equipment
        ).order_by('?')[:exercises_per_day]
    else:
        # กรณีฝึกทั้งร่างกาย
        # สร้างรายการท่าที่ครอบคลุมทุกส่วนของร่างกาย
        muscle_groups = ['chest', 'back', 'shoulders', 'arms', 'legs', 'core']
        exercises = []
        
        # เลือกท่าจากแต่ละกลุ่มกล้ามเนื้อ
        for i, muscle_group in enumerate(muscle_groups):
            if i >= exercises_per_day:
                break
                
            exercise = Exercise.objects.filter(
                muscle_group=muscle_group,
                difficulty__in=[difficulty, 'beginner'] if difficulty != 'beginner' else ['beginner'],
                equipment_required=exercise_plan.available_equipment
            ).order_by('?').first()
            
            if exercise:
                exercises.append(exercise)
        
        # เพิ่มท่าออกกำลังกายจนครบตามจำนวน
        remaining = exercises_per_day - len(exercises)
        if remaining > 0:
            additional_exercises = Exercise.objects.filter(
                difficulty__in=[difficulty, 'beginner'] if difficulty != 'beginner' else ['beginner'],
                equipment_required=exercise_plan.available_equipment
            ).exclude(id__in=[e.id for e in exercises]).order_by('?')[:remaining]
            
            exercises.extend(additional_exercises)
    
    # สร้างรายการออกกำลังกาย
    for i, exercise in enumerate(exercises):
        WorkoutExercise.objects.create(
            workout_day=workout_day,
            exercise=exercise,
            sets=sets,
            reps=reps,
            rest_time=rest_time,
            order=i + 1
        )