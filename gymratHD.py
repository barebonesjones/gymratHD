"""
gymratHD - The Ultimate Mike Mentzer Training & Nutrition Tracker
================================================================

Real workout tracking, real nutrition logging, real progress analysis.

Created by: github.com/barebonesjones
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import json
import csv
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime, timedelta
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AppColors:
    """Professional color system"""
    ELECTRIC_BLUE = "#0047FF"
    CROWN_GOLD = "#FFD700"
    ENERGY_RED = "#FF0000"
    NEON_GREEN = "#39FF14"
    FIRE_ORANGE = "#FF4500"
    CONCRETE_GRAY = "#2B2B2B"
    PRIMARY_TEXT = "#FFFFFF"
    SECONDARY_TEXT = "#CCCCCC"
    DEEP_BLACK = "#000000"
    LIGHT_GRAY = "#404040"

class MentzerProtocols:
    """Authentic Mike Mentzer Heavy Duty protocols"""
    
    # Verified nutrition ratios
    CARB_PERCENT = 60
    PROTEIN_PERCENT = 25
    FAT_PERCENT = 15
    PROTEIN_PER_KG = 1.0
    
    # Recovery periods
    RECOVERY_HOURS = {
        'Beginner': 72,
        'Intermediate': 96,
        'Advanced': 168
    }
    
    @staticmethod
    def calculate_nutrition(weight_kg: float, tdee: float, phase: str) -> Dict:
        """Calculate Mentzer's exact nutrition protocol"""
        if phase == "Bulking":
            calories = int(tdee * 1.15)
        elif phase == "Cutting":
            calories = int(tdee * 0.85)
        else:
            calories = int(tdee)
        
        carb_cals = calories * (MentzerProtocols.CARB_PERCENT / 100)
        protein_cals = calories * (MentzerProtocols.PROTEIN_PERCENT / 100)
        fat_cals = calories * (MentzerProtocols.FAT_PERCENT / 100)
        
        carbs = carb_cals / 4
        protein = min(protein_cals / 4, weight_kg * MentzerProtocols.PROTEIN_PER_KG)
        fat = fat_cals / 9
        
        # Redistribute excess protein calories to carbs
        if protein < protein_cals / 4:
            excess_cals = (protein_cals / 4 - protein) * 4
            carbs += excess_cals / 4
        
        return {
            'calories': calories,
            'carbs': round(carbs, 1),
            'protein': round(protein, 1),
            'fat': round(fat, 1)
        }

class TrainingParameters:
    """General training parameters (not specific to Mentzer)"""
    
    TRAINING_GOALS = {
        'Strength': {
            'rep_range': (1, 5),
            'rest_seconds': (180, 300),
            'sets': (3, 5),
            'focus': 'Maximum load, perfect form'
        },
        'Hypertrophy': {
            'rep_range': (6, 12),
            'rest_seconds': (60, 120),
            'sets': (1, 3),
            'focus': 'Time under tension, failure'
        },
        'Power': {
            'rep_range': (3, 6),
            'rest_seconds': (120, 240),
            'sets': (3, 6),
            'focus': 'Explosive movement, speed'
        },
        'Endurance': {
            'rep_range': (12, 20),
            'rest_seconds': (30, 60),
            'sets': (2, 4),
            'focus': 'Metabolic stress, volume'
        }
    }

class DataManager:
    """Complete data management system"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        for subdir in ["workouts", "nutrition", "progress", "exports"]:
            (self.data_dir / subdir).mkdir(exist_ok=True)
        
        # Initialize CSV files
        self._initialize_csv_files()
    
    def _initialize_csv_files(self):
        """Initialize CSV files with headers"""
        workout_csv = self.data_dir / "workouts" / "workout_log.csv"
        if not workout_csv.exists():
            with open(workout_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Exercise', 'Sets', 'Reps', 'Weight', 'RPE', 'Mode', 'Goal', 'Duration'])
        
        nutrition_csv = self.data_dir / "nutrition" / "nutrition_log.csv"
        if not nutrition_csv.exists():
            with open(nutrition_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Time', 'Food', 'Quantity_g', 'Calories', 'Protein', 'Carbs', 'Fat', 'Meal_Type'])
    
    def save_workout(self, workout_data: Dict) -> bool:
        """Save workout to CSV"""
        try:
            workout_csv = self.data_dir / "workouts" / "workout_log.csv"
            with open(workout_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for exercise in workout_data['exercises']:
                    for set_data in exercise['sets']:
                        writer.writerow([
                            workout_data['date'],
                            exercise['name'],
                            set_data.get('set_number', 1),
                            set_data.get('reps', 0),
                            set_data.get('weight', 0),
                            set_data.get('rpe', 0),
                            workout_data.get('mode', 'General'),
                            workout_data.get('goal', 'Hypertrophy'),
                            workout_data.get('duration', 0)
                        ])
            return True
        except Exception as e:
            print(f"Error saving workout: {e}")
            return False
    
    def save_nutrition(self, nutrition_data: Dict) -> bool:
        """Save nutrition entry to CSV"""
        try:
            nutrition_csv = self.data_dir / "nutrition" / "nutrition_log.csv"
            with open(nutrition_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    nutrition_data['date'],
                    nutrition_data['time'],
                    nutrition_data['food'],
                    nutrition_data['quantity'],
                    nutrition_data['calories'],
                    nutrition_data['protein'],
                    nutrition_data['carbs'],
                    nutrition_data['fat'],
                    nutrition_data.get('meal_type', 'Other')
                ])
            return True
        except Exception as e:
            print(f"Error saving nutrition: {e}")
            return False
    
    def get_workout_data(self, days: int = 30) -> pd.DataFrame:
        """Get workout data for analysis"""
        try:
            workout_csv = self.data_dir / "workouts" / "workout_log.csv"
            if workout_csv.exists():
                df = pd.read_csv(workout_csv)
                df['Date'] = pd.to_datetime(df['Date'])
                cutoff = datetime.now() - timedelta(days=days)
                return df[df['Date'] >= cutoff]
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()
    
    def get_nutrition_data(self, days: int = 30) -> pd.DataFrame:
        """Get nutrition data for analysis"""
        try:
            nutrition_csv = self.data_dir / "nutrition" / "nutrition_log.csv"
            if nutrition_csv.exists():
                df = pd.read_csv(nutrition_csv)
                df['Date'] = pd.to_datetime(df['Date'])
                cutoff = datetime.now() - timedelta(days=days)
                return df[df['Date'] >= cutoff]
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()
    
    def save_user_profile(self, profile_data: Dict) -> bool:
        """Save user profile"""
        try:
            profile_file = self.data_dir / "user_profile.json"
            profile_data['last_updated'] = datetime.now().isoformat()
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2)
            return True
        except Exception:
            return False
    
    def load_user_profile(self) -> Dict:
        """Load user profile with defaults"""
        default_profile = {
            'weight': 70.0, 'height': 170.0, 'age': 25, 'gender': 'Male',
            'activity_level': 'Moderate', 'experience_level': 'Beginner',
            'mode': 'Heavy Duty', 'phase': 'Maintenance', 'goals': ['Hypertrophy']
        }
        
        try:
            profile_file = self.data_dir / "user_profile.json"
            if profile_file.exists():
                with open(profile_file, 'r', encoding='utf-8') as f:
                    loaded_profile = json.load(f)
                    default_profile.update(loaded_profile)
        except Exception:
            pass
        
        return default_profile

class WorkoutWindow(ctk.CTkToplevel):
    """Real workout tracking window"""
    
    def __init__(self, parent, data_manager, user_profile):
        super().__init__(parent)
        self.parent = parent
        self.data_manager = data_manager
        self.user_profile = user_profile
        
        self.title("gymratHD - Workout Tracking")
        self.geometry("1000x700")
        self.configure(fg_color=AppColors.DEEP_BLACK)
        
        # Current workout data
        self.current_workout = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'start_time': datetime.now(),
            'exercises': [],
            'mode': user_profile.get('mode', 'Heavy Duty'),
            'goal': user_profile.get('goals', ['Hypertrophy'])[0] if isinstance(user_profile.get('goals'), list) else user_profile.get('goals', 'Hypertrophy')
        }
        
        self.transient(parent)
        self.grab_set()
        
        self._create_workout_interface()
    
    def _create_workout_interface(self):
        """Create workout interface"""
        # Header
        header_frame = ctk.CTkFrame(self, height=60)
        header_frame.pack(fill="x", padx=10, pady=10)
        header_frame.grid_propagate(False)
        
        ctk.CTkLabel(
            header_frame,
            text="⟨ WORKOUT TRACKING ⟩",
            font=("Arial", 20, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).pack(side="left", padx=20, pady=15)
        
        # Workout info - simplified
        info_text = f"Goal: {self.current_workout['goal']} • {self.current_workout['date']}"
        ctk.CTkLabel(
            header_frame,
            text=info_text,
            font=("Arial", 12),
            text_color=AppColors.PRIMARY_TEXT
        ).pack(side="right", padx=20, pady=15)
        
        # Main content frame
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        content_frame.grid_columnconfigure(0, weight=2)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Left side - Exercise entry
        self._create_exercise_entry(content_frame)
        
        # Right side - Current workout
        self._create_workout_display(content_frame)
    
    def _create_exercise_entry(self, parent):
        """Exercise entry section"""
        entry_frame = ctk.CTkFrame(parent)
        entry_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        entry_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        ctk.CTkLabel(
            entry_frame,
            text="⟨ ADD EXERCISE ⟩",
            font=("Arial", 16, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).grid(row=0, column=0, columnspan=2, pady=(15, 20))
        
        # Exercise name
        ctk.CTkLabel(entry_frame, text="Exercise:", text_color=AppColors.CROWN_GOLD).grid(row=1, column=0, sticky="w", padx=15, pady=5)
        self.exercise_name = ctk.CTkEntry(entry_frame, placeholder_text="e.g., Dumbbell Press")
        self.exercise_name.grid(row=1, column=1, sticky="ew", padx=15, pady=5)
        
        # Training parameters display
        params_frame = ctk.CTkFrame(entry_frame)
        params_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=10)
        
        current_goal = self.current_workout['goal']
        params = TrainingParameters.TRAINING_GOALS.get(current_goal, TrainingParameters.TRAINING_GOALS['Hypertrophy'])
        
        params_text = f"{current_goal} Parameters: {params['rep_range'][0]}-{params['rep_range'][1]} reps • {params['focus']}"
        ctk.CTkLabel(
            params_frame,
            text=params_text,
            font=("Arial", 10),
            text_color=AppColors.SECONDARY_TEXT,
            wraplength=400
        ).pack(pady=10, padx=10)
        
        # Set details
        set_frame = ctk.CTkFrame(entry_frame)
        set_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=15, pady=10)
        set_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Headers
        headers = ["Reps", "Weight (lbs)", "RPE (1-10)", ""]
        for i, header in enumerate(headers):
            ctk.CTkLabel(set_frame, text=header, text_color=AppColors.CROWN_GOLD, font=("Arial", 11, "bold")).grid(row=0, column=i, padx=5, pady=5)
        
        # Set entry fields
        self.set_entries = []
        for i in range(5):  # 5 potential sets
            reps_entry = ctk.CTkEntry(set_frame, width=60, placeholder_text="12")
            weight_entry = ctk.CTkEntry(set_frame, width=80, placeholder_text="50")
            rpe_entry = ctk.CTkEntry(set_frame, width=60, placeholder_text="8")
            
            reps_entry.grid(row=i+1, column=0, padx=5, pady=2)
            weight_entry.grid(row=i+1, column=1, padx=5, pady=2)
            rpe_entry.grid(row=i+1, column=2, padx=5, pady=2)
            
            self.set_entries.append({
                'reps': reps_entry,
                'weight': weight_entry,
                'rpe': rpe_entry
            })
        
        # Add exercise button
        add_button = ctk.CTkButton(
            entry_frame,
            text="⟨ ADD EXERCISE ⟩",
            command=self._add_exercise,
            fg_color=AppColors.NEON_GREEN,
            text_color=AppColors.DEEP_BLACK,
            font=("Arial", 12, "bold"),
            height=40
        )
        add_button.grid(row=4, column=0, columnspan=2, pady=20, padx=15, sticky="ew")
        
        # Templates based on mode
        if self.current_workout['mode'] == 'Heavy Duty':
            self._create_heavy_duty_templates(entry_frame)
        else:
            self._create_general_templates(entry_frame)
    
    def _create_heavy_duty_templates(self, parent):
        """Heavy Duty specific templates"""
        templates_frame = ctk.CTkFrame(parent)
        templates_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=15, pady=10)
        
        ctk.CTkLabel(
            templates_frame,
            text="⟨ HEAVY DUTY TEMPLATES ⟩",
            font=("Arial", 12, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).pack(pady=10)
        
        templates = [
            "Chest: Flyes → Dumbbell Press",
            "Back: Pullovers → Dumbbell Rows",
            "Shoulders: Lateral Raises → Press",
            "Arms: Curls + Tricep Extensions"
        ]
        
        for template in templates:
            ctk.CTkButton(
                templates_frame,
                text=template,
                command=lambda t=template: self._apply_template(t),
                fg_color=AppColors.ELECTRIC_BLUE,
                height=30,
                font=("Arial", 10)
            ).pack(fill="x", padx=10, pady=2)
    
    def _create_general_templates(self, parent):
        """General training templates"""
        templates_frame = ctk.CTkFrame(parent)
        templates_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=15, pady=10)
        
        ctk.CTkLabel(
            templates_frame,
            text=f"⟨ {self.current_workout['goal'].upper()} TEMPLATES ⟩",
            font=("Arial", 12, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).pack(pady=10)
        
        goal = self.current_workout['goal']
        if goal == 'Strength':
            templates = ["Squat", "Deadlift", "Bench Press", "Overhead Press"]
        elif goal == 'Power':
            templates = ["Power Clean", "Jump Squat", "Medicine Ball Throw", "Explosive Push-up"]
        elif goal == 'Endurance':
            templates = ["Circuit Training", "High Rep Squats", "Burpees", "Mountain Climbers"]
        else:  # Hypertrophy
            templates = ["Dumbbell Press", "Dumbbell Rows", "Squats", "Pull-ups"]
        
        for template in templates:
            ctk.CTkButton(
                templates_frame,
                text=template,
                command=lambda t=template: self._apply_general_template(t),
                fg_color=AppColors.FIRE_ORANGE,
                height=30,
                font=("Arial", 10)
            ).pack(fill="x", padx=10, pady=2)
    
    def _create_workout_display(self, parent):
        """Current workout display"""
        display_frame = ctk.CTkFrame(parent)
        display_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        
        # Title
        ctk.CTkLabel(
            display_frame,
            text="⟨ CURRENT WORKOUT ⟩",
            font=("Arial", 16, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).pack(pady=(15, 10))
        
        # Workout summary
        self.workout_summary = ctk.CTkTextbox(display_frame, height=400, font=("Arial", 11))
        self.workout_summary.pack(fill="both", expand=True, padx=15, pady=10)
        self._update_workout_display()
        
        # Action buttons
        button_frame = ctk.CTkFrame(display_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkButton(
            button_frame,
            text="⟨ FINISH WORKOUT ⟩",
            command=self._finish_workout,
            fg_color=AppColors.ENERGY_RED,
            text_color=AppColors.PRIMARY_TEXT,
            font=("Arial", 12, "bold"),
            height=40
        ).pack(fill="x", pady=(0, 5))
        
        ctk.CTkButton(
            button_frame,
            text="⟨ CANCEL ⟩",
            command=self.destroy,
            fg_color=AppColors.CONCRETE_GRAY,
            text_color=AppColors.PRIMARY_TEXT,
            font=("Arial", 12, "bold"),
            height=35
        ).pack(fill="x")
    
    def _add_exercise(self):
        """Add exercise to current workout"""
        exercise_name = self.exercise_name.get().strip()
        if not exercise_name:
            messagebox.showwarning("Missing Exercise", "Please enter an exercise name.")
            return
        
        # Collect sets data
        sets_data = []
        for i, entry_set in enumerate(self.set_entries):
            reps = entry_set['reps'].get().strip()
            weight = entry_set['weight'].get().strip()
            rpe = entry_set['rpe'].get().strip()
            
            if reps or weight or rpe:  # If any field has data
                try:
                    sets_data.append({
                        'set_number': i + 1,
                        'reps': int(reps) if reps else 0,
                        'weight': float(weight) if weight else 0,
                        'rpe': int(rpe) if rpe else 0
                    })
                except ValueError:
                    messagebox.showerror("Invalid Data", f"Please enter valid numbers for set {i+1}")
                    return
        
        if not sets_data:
            messagebox.showwarning("No Sets", "Please enter at least one set of data.")
            return
        
        # Add to current workout
        self.current_workout['exercises'].append({
            'name': exercise_name,
            'sets': sets_data
        })
        
        # Clear form
        self.exercise_name.delete(0, 'end')
        for entry_set in self.set_entries:
            entry_set['reps'].delete(0, 'end')
            entry_set['weight'].delete(0, 'end')
            entry_set['rpe'].delete(0, 'end')
        
        # Update display
        self._update_workout_display()
    
    def _apply_template(self, template):
        """Apply Heavy Duty template"""
        if "Chest:" in template:
            self.exercise_name.delete(0, 'end')
            self.exercise_name.insert(0, "Dumbbell Flyes")
            messagebox.showinfo("Template Applied", "Added Dumbbell Flyes. Perform to failure, then immediately do Dumbbell Press.")
        elif "Back:" in template:
            self.exercise_name.delete(0, 'end')
            self.exercise_name.insert(0, "Dumbbell Pullovers")
            messagebox.showinfo("Template Applied", "Added Dumbbell Pullovers. Pre-exhaust the lats, then do Dumbbell Rows.")
        elif "Shoulders:" in template:
            self.exercise_name.delete(0, 'end')
            self.exercise_name.insert(0, "Lateral Raises")
            messagebox.showinfo("Template Applied", "Added Lateral Raises. Pre-exhaust delts, then do Shoulder Press.")
        elif "Arms:" in template:
            self.exercise_name.delete(0, 'end')
            self.exercise_name.insert(0, "Dumbbell Curls")
            messagebox.showinfo("Template Applied", "Added Dumbbell Curls. Follow with Tricep Extensions for complete arm training.")
    
    def _apply_general_template(self, template):
        """Apply general template"""
        self.exercise_name.delete(0, 'end')
        self.exercise_name.insert(0, template)
        
        goal = self.current_workout['goal']
        params = TrainingParameters.TRAINING_GOALS.get(goal, TrainingParameters.TRAINING_GOALS['Hypertrophy'])
        rep_range = params['rep_range']
        
        messagebox.showinfo("Template Applied", f"Added {template}. Target: {rep_range[0]}-{rep_range[1]} reps for {goal}.")
    
    def _update_workout_display(self):
        """Update workout display"""
        self.workout_summary.delete("1.0", "end")
        
        if not self.current_workout['exercises']:
            self.workout_summary.insert("1.0", "No exercises added yet.\n\nUse the form on the left to add exercises and sets.")
            return
        
        display_text = f"Workout Summary\n{'-' * 30}\n\n"
        
        total_sets = 0
        total_volume = 0
        
        for i, exercise in enumerate(self.current_workout['exercises'], 1):
            display_text += f"{i}. {exercise['name']}\n"
            
            for set_data in exercise['sets']:
                reps = set_data['reps']
                weight = set_data['weight']
                rpe = set_data['rpe']
                volume = reps * weight
                
                display_text += f"   Set {set_data['set_number']}: {reps} reps × {weight} lbs"
                if rpe > 0:
                    display_text += f" @ RPE {rpe}"
                display_text += f" (Vol: {volume})\n"
                
                total_sets += 1
                total_volume += volume
            
            display_text += "\n"
        
        # Summary stats
        elapsed = datetime.now() - self.current_workout['start_time']
        duration_min = int(elapsed.total_seconds() / 60)
        
        display_text += f"Summary:\n"
        display_text += f"• Total Sets: {total_sets}\n"
        display_text += f"• Total Volume: {total_volume:,.0f} lbs\n"
        display_text += f"• Duration: {duration_min} minutes\n"
        display_text += f"• Goal: {self.current_workout['goal']}"
        
        self.workout_summary.insert("1.0", display_text)
    
    def _finish_workout(self):
        """Save and finish workout"""
        if not self.current_workout['exercises']:
            messagebox.showwarning("Empty Workout", "Add at least one exercise before finishing.")
            return
        
        # Calculate duration
        elapsed = datetime.now() - self.current_workout['start_time']
        self.current_workout['duration'] = int(elapsed.total_seconds() / 60)
        
        # Save workout
        if self.data_manager.save_workout(self.current_workout):
            messagebox.showinfo("Workout Saved", f"Workout completed!\n\nDuration: {self.current_workout['duration']} minutes\nExercises: {len(self.current_workout['exercises'])}")
            self.destroy()
        else:
            messagebox.showerror("Save Error", "Failed to save workout. Please try again.")

class NutritionWindow(ctk.CTkToplevel):
    """Real nutrition tracking window"""
    
    def __init__(self, parent, data_manager, user_profile, food_database):
        super().__init__(parent)
        self.parent = parent
        self.data_manager = data_manager
        self.user_profile = user_profile
        self.food_database = food_database
        
        self.title("gymratHD - Nutrition Tracking")
        self.geometry("1000x700")
        self.configure(fg_color=AppColors.DEEP_BLACK)
        
        # Today's nutrition data
        self.daily_nutrition = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
        self.nutrition_targets = self._calculate_targets()
        
        self.transient(parent)
        self.grab_set()
        
        self._create_nutrition_interface()
        self._load_todays_nutrition()
    
    def _calculate_targets(self):
        """Calculate nutrition targets"""
        try:
            weight = self.user_profile.get('weight', 70)
            height = self.user_profile.get('height', 170)
            age = self.user_profile.get('age', 25)
            gender = self.user_profile.get('gender', 'Male')
            activity = self.user_profile.get('activity_level', 'Moderate')
            phase = self.user_profile.get('phase', 'Maintenance')
            
            # Calculate BMR
            if gender == 'Male':
                bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
            else:
                bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
            
            # Calculate TDEE
            multipliers = {'Sedentary': 1.2, 'Light': 1.375, 'Moderate': 1.55, 'Very Active': 1.725}
            tdee = bmr * multipliers.get(activity, 1.55)
            
            # Use Mentzer protocols
            return MentzerProtocols.calculate_nutrition(weight, tdee, phase)
        except:
            return {'calories': 2000, 'carbs': 300, 'protein': 125, 'fat': 67}
    
    def _create_nutrition_interface(self):
        """Create nutrition interface"""
        # Header
        header_frame = ctk.CTkFrame(self, height=60)
        header_frame.pack(fill="x", padx=10, pady=10)
        header_frame.grid_propagate(False)
        
        ctk.CTkLabel(
            header_frame,
            text="⟨ NUTRITION TRACKING ⟩",
            font=("Arial", 20, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).pack(side="left", padx=20, pady=15)
        
        # Today's date
        today = datetime.now().strftime('%Y-%m-%d')
        ctk.CTkLabel(
            header_frame,
            text=f"Today: {today}",
            font=("Arial", 12),
            text_color=AppColors.PRIMARY_TEXT
        ).pack(side="right", padx=20, pady=15)
        
        # Main content
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        content_frame.grid_columnconfigure(0, weight=2)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Left side - Food entry
        self._create_food_entry(content_frame)
        
        # Right side - Daily summary
        self._create_daily_summary(content_frame)
    
    def _create_food_entry(self, parent):
        """Food entry section"""
        entry_frame = ctk.CTkFrame(parent)
        entry_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        entry_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        ctk.CTkLabel(
            entry_frame,
            text="⟨ ADD FOOD ⟩",
            font=("Arial", 16, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).grid(row=0, column=0, columnspan=2, pady=(15, 20))
        
        # Food selection
        ctk.CTkLabel(entry_frame, text="Food Category:", text_color=AppColors.CROWN_GOLD).grid(row=1, column=0, sticky="w", padx=15, pady=5)
        
        # Get food categories
        categories = [key for key in self.food_database.keys() if isinstance(self.food_database[key], dict)]
        
        self.category_var = tk.StringVar(value=categories[0] if categories else "")
        category_menu = ctk.CTkOptionMenu(entry_frame, values=categories, variable=self.category_var, command=self._update_food_list)
        category_menu.grid(row=1, column=1, sticky="ew", padx=15, pady=5)
        
        # Food item
        ctk.CTkLabel(entry_frame, text="Food Item:", text_color=AppColors.CROWN_GOLD).grid(row=2, column=0, sticky="w", padx=15, pady=5)
        self.food_var = tk.StringVar()
        self.food_menu = ctk.CTkOptionMenu(entry_frame, values=[], variable=self.food_var)
        self.food_menu.grid(row=2, column=1, sticky="ew", padx=15, pady=5)
        
        # Quantity
        ctk.CTkLabel(entry_frame, text="Quantity (grams):", text_color=AppColors.CROWN_GOLD).grid(row=3, column=0, sticky="w", padx=15, pady=5)
        self.quantity_entry = ctk.CTkEntry(entry_frame, placeholder_text="100")
        self.quantity_entry.grid(row=3, column=1, sticky="ew", padx=15, pady=5)
        
        # Meal type
        ctk.CTkLabel(entry_frame, text="Meal Type:", text_color=AppColors.CROWN_GOLD).grid(row=4, column=0, sticky="w", padx=15, pady=5)
        self.meal_var = tk.StringVar(value="Breakfast")
        meal_menu = ctk.CTkOptionMenu(entry_frame, values=["Breakfast", "Lunch", "Dinner", "Snack", "Pre-Workout", "Post-Workout"], variable=self.meal_var)
        meal_menu.grid(row=4, column=1, sticky="ew", padx=15, pady=5)
        
        # Add food button
        add_button = ctk.CTkButton(
            entry_frame,
            text="⟨ ADD FOOD ⟩",
            command=self._add_food,
            fg_color=AppColors.NEON_GREEN,
            text_color=AppColors.DEEP_BLACK,
            font=("Arial", 12, "bold"),
            height=40
        )
        add_button.grid(row=5, column=0, columnspan=2, pady=20, padx=15, sticky="ew")
        
        # Preview frame
        preview_frame = ctk.CTkFrame(entry_frame)
        preview_frame.grid(row=6, column=0, columnspan=2, sticky="ew", padx=15, pady=10)
        
        ctk.CTkLabel(
            preview_frame,
            text="⟨ NUTRITION PREVIEW ⟩",
            font=("Arial", 12, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).pack(pady=(10, 5))
        
        self.preview_label = ctk.CTkLabel(
            preview_frame,
            text="Select food and quantity to see nutrition info",
            font=("Arial", 10),
            text_color=AppColors.SECONDARY_TEXT
        )
        self.preview_label.pack(pady=(0, 10))
        
        # Update food list initially
        self._update_food_list(categories[0] if categories else "")
        
        # Bind quantity change to update preview
        self.quantity_entry.bind('<KeyRelease>', self._update_preview)
        self.food_var.trace('w', lambda *args: self._update_preview())
    
    def _create_daily_summary(self, parent):
        """Daily nutrition summary"""
        summary_frame = ctk.CTkFrame(parent)
        summary_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        
        # Title
        ctk.CTkLabel(
            summary_frame,
            text="⟨ DAILY SUMMARY ⟩",
            font=("Arial", 16, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).pack(pady=(15, 10))
        
        # Targets vs actual
        self.summary_text = ctk.CTkTextbox(summary_frame, height=300, font=("Arial", 11))
        self.summary_text.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Today's foods list
        foods_frame = ctk.CTkFrame(summary_frame)
        foods_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(
            foods_frame,
            text="⟨ TODAY'S FOODS ⟩",
            font=("Arial", 12, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).pack(pady=(10, 5))
        
        self.foods_listbox = tk.Listbox(foods_frame, bg=AppColors.CONCRETE_GRAY, fg=AppColors.PRIMARY_TEXT, 
                                       selectbackground=AppColors.ELECTRIC_BLUE, font=("Arial", 9))
        self.foods_listbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Update summary
        self._update_daily_summary()
    
    def _update_food_list(self, category):
        """Update food list based on category"""
        if category in self.food_database:
            foods = list(self.food_database[category].keys())
            self.food_menu.configure(values=foods)
            if foods:
                self.food_var.set(foods[0])
        self._update_preview()
    
    def _update_preview(self, event=None):
        """Update nutrition preview"""
        try:
            category = self.category_var.get()
            food = self.food_var.get()
            quantity = self.quantity_entry.get()
            
            if not all([category, food, quantity]):
                return
                
            quantity = float(quantity)
            
            if category in self.food_database and food in self.food_database[category]:
                food_data = self.food_database[category][food]
                
                # Calculate nutrition per quantity
                calories = food_data['calories'] * quantity
                protein = food_data['protein'] * quantity
                carbs = food_data['carbs'] * quantity
                fat = food_data['fat'] * quantity
                
                preview_text = f"{quantity}g of {food}:\n"
                preview_text += f"Calories: {calories:.0f}\n"
                preview_text += f"Protein: {protein:.1f}g\n"
                preview_text += f"Carbs: {carbs:.1f}g\n"
                preview_text += f"Fat: {fat:.1f}g"
                
                self.preview_label.configure(text=preview_text)
            else:
                self.preview_label.configure(text="Food data not available")
                
        except ValueError:
            self.preview_label.configure(text="Enter valid quantity")
        except Exception:
            self.preview_label.configure(text="Error calculating nutrition")
    
    def _add_food(self):
        """Add food to daily log"""
        try:
            category = self.category_var.get()
            food = self.food_var.get()
            quantity = float(self.quantity_entry.get())
            meal_type = self.meal_var.get()
            
            if not all([category, food, quantity]):
                messagebox.showwarning("Incomplete Data", "Please select food and enter quantity.")
                return
            
            if category in self.food_database and food in self.food_database[category]:
                food_data = self.food_database[category][food]
                
                # Calculate nutrition
                calories = food_data['calories'] * quantity
                protein = food_data['protein'] * quantity
                carbs = food_data['carbs'] * quantity
                fat = food_data['fat'] * quantity
                
                # Prepare nutrition entry
                nutrition_entry = {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'food': food,
                    'quantity': quantity,
                    'calories': calories,
                    'protein': protein,
                    'carbs': carbs,
                    'fat': fat,
                    'meal_type': meal_type
                }
                
                # Save to database
                if self.data_manager.save_nutrition(nutrition_entry):
                    # Update daily totals
                    self.daily_nutrition['calories'] += calories
                    self.daily_nutrition['protein'] += protein
                    self.daily_nutrition['carbs'] += carbs
                    self.daily_nutrition['fat'] += fat
                    
                    # Clear form
                    self.quantity_entry.delete(0, 'end')
                    
                    # Update displays
                    self._update_daily_summary()
                    self._load_todays_nutrition()
                    
                    messagebox.showinfo("Food Added", f"Added {quantity}g of {food} to {meal_type}")
                else:
                    messagebox.showerror("Save Error", "Failed to save food entry.")
            else:
                messagebox.showerror("Food Not Found", "Selected food not found in database.")
                
        except ValueError:
            messagebox.showerror("Invalid Quantity", "Please enter a valid quantity in grams.")
        except Exception as e:
            messagebox.showerror("Error", f"Error adding food: {e}")
    
    def _load_todays_nutrition(self):
        """Load today's nutrition data"""
        try:
            today_data = self.data_manager.get_nutrition_data(days=1)
            today = datetime.now().strftime('%Y-%m-%d')
            today_foods = today_data[today_data['Date'].dt.strftime('%Y-%m-%d') == today]
            
            # Reset daily totals
            self.daily_nutrition = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
            
            # Clear foods list
            self.foods_listbox.delete(0, tk.END)
            
            # Add each food entry
            for _, food_entry in today_foods.iterrows():
                self.daily_nutrition['calories'] += food_entry['Calories']
                self.daily_nutrition['protein'] += food_entry['Protein']
                self.daily_nutrition['carbs'] += food_entry['Carbs']
                self.daily_nutrition['fat'] += food_entry['Fat']
                
                # Add to listbox
                display_text = f"{food_entry['Time']} - {food_entry['Food']} ({food_entry['Quantity_g']}g) - {food_entry['Meal_Type']}"
                self.foods_listbox.insert(tk.END, display_text)
            
            self._update_daily_summary()
            
        except Exception as e:
            print(f"Error loading today's nutrition: {e}")
    
    def _update_daily_summary(self):
        """Update daily summary display"""
        # Calculate percentages
        cal_percent = (self.daily_nutrition['calories'] / self.nutrition_targets['calories']) * 100 if self.nutrition_targets['calories'] > 0 else 0
        protein_percent = (self.daily_nutrition['protein'] / self.nutrition_targets['protein']) * 100 if self.nutrition_targets['protein'] > 0 else 0
        carbs_percent = (self.daily_nutrition['carbs'] / self.nutrition_targets['carbs']) * 100 if self.nutrition_targets['carbs'] > 0 else 0
        fat_percent = (self.daily_nutrition['fat'] / self.nutrition_targets['fat']) * 100 if self.nutrition_targets['fat'] > 0 else 0
        
        # Create summary text
        mode = self.user_profile.get('mode', 'Heavy Duty')
        if mode == 'Heavy Duty':
            summary_text = "MENTZER'S 60/25/15 PROTOCOL\n"
            summary_text += "=" * 30 + "\n\n"
        else:
            summary_text = "NUTRITION TARGETS\n"
            summary_text += "=" * 20 + "\n\n"
        
        summary_text += f"CALORIES:\n"
        summary_text += f"  {self.daily_nutrition['calories']:.0f} / {self.nutrition_targets['calories']:.0f} ({cal_percent:.1f}%)\n\n"
        
        summary_text += f"PROTEIN:\n"
        summary_text += f"  {self.daily_nutrition['protein']:.1f}g / {self.nutrition_targets['protein']:.1f}g ({protein_percent:.1f}%)\n"
        if mode == 'Heavy Duty':
            summary_text += f"  (25% of calories - moderate approach)\n\n"
        else:
            summary_text += "\n"
        
        summary_text += f"CARBS:\n"
        summary_text += f"  {self.daily_nutrition['carbs']:.1f}g / {self.nutrition_targets['carbs']:.1f}g ({carbs_percent:.1f}%)\n"
        if mode == 'Heavy Duty':
            summary_text += f"  (60% of calories - fuel for training)\n\n"
        else:
            summary_text += "\n"
        
        summary_text += f"FAT:\n"
        summary_text += f"  {self.daily_nutrition['fat']:.1f}g / {self.nutrition_targets['fat']:.1f}g ({fat_percent:.1f}%)\n"
        if mode == 'Heavy Duty':
            summary_text += f"  (15% of calories - hormonal support)\n\n"
        else:
            summary_text += "\n"
        
        # Overall status
        overall_percent = (cal_percent + protein_percent + carbs_percent + fat_percent) / 4
        if overall_percent >= 90:
            summary_text += "STATUS: Excellent adherence! 🎯"
        elif overall_percent >= 70:
            summary_text += "STATUS: Good progress 👍"
        elif overall_percent >= 50:
            summary_text += "STATUS: Keep adding foods 📈"
        else:
            summary_text += "STATUS: Just getting started 🚀"
        
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", summary_text)

class ProgressWindow(ctk.CTkToplevel):
    """Real progress analysis window"""
    
    def __init__(self, parent, data_manager, user_profile):
        super().__init__(parent)
        self.parent = parent
        self.data_manager = data_manager
        self.user_profile = user_profile
        
        self.title("gymratHD - Progress Analysis")
        self.geometry("1200x800")
        self.configure(fg_color=AppColors.DEEP_BLACK)
        
        self.transient(parent)
        self.grab_set()
        
        self._create_progress_interface()
    
    def _create_progress_interface(self):
        """Create progress analysis interface"""
        # Header
        header_frame = ctk.CTkFrame(self, height=60)
        header_frame.pack(fill="x", padx=10, pady=10)
        header_frame.grid_propagate(False)
        
        ctk.CTkLabel(
            header_frame,
            text="⟨ PROGRESS ANALYSIS ⟩",
            font=("Arial", 20, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).pack(side="left", padx=20, pady=15)
        
        # Time period selector
        period_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        period_frame.pack(side="right", padx=20, pady=15)
        
        ctk.CTkLabel(period_frame, text="Period:", text_color=AppColors.CROWN_GOLD).pack(side="left", padx=5)
        self.period_var = tk.StringVar(value="30 days")
        period_menu = ctk.CTkOptionMenu(period_frame, values=["7 days", "30 days", "90 days", "All time"], 
                                       variable=self.period_var, command=self._update_analysis)
        period_menu.pack(side="left", padx=5)
        
        # Main content with tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Create tabs
        self._create_workout_analysis_tab()
        self._create_nutrition_analysis_tab()
        self._create_summary_tab()
        
        # Initial analysis
        self._update_analysis("30 days")
    
    def _create_workout_analysis_tab(self):
        """Workout analysis tab"""
        workout_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(workout_frame, text="Workout Analysis")
        
        # Split into left (charts) and right (stats)
        workout_frame.grid_columnconfigure(0, weight=2)
        workout_frame.grid_columnconfigure(1, weight=1)
        workout_frame.grid_rowconfigure(0, weight=1)
        
        # Charts frame
        charts_frame = ctk.CTkFrame(workout_frame)
        charts_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        self.workout_charts_frame = charts_frame
        
        # Stats frame
        stats_frame = ctk.CTkFrame(workout_frame)
        stats_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        
        ctk.CTkLabel(
            stats_frame,
            text="⟨ WORKOUT STATS ⟩",
            font=("Arial", 16, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).pack(pady=(15, 10))
        
        self.workout_stats_text = ctk.CTkTextbox(stats_frame, font=("Arial", 11))
        self.workout_stats_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
    
    def _create_nutrition_analysis_tab(self):
        """Nutrition analysis tab"""
        nutrition_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(nutrition_frame, text="Nutrition Analysis")
        
        nutrition_frame.grid_columnconfigure(0, weight=2)
        nutrition_frame.grid_columnconfigure(1, weight=1)
        nutrition_frame.grid_rowconfigure(0, weight=1)
        
        # Charts frame
        charts_frame = ctk.CTkFrame(nutrition_frame)
        charts_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        self.nutrition_charts_frame = charts_frame
        
        # Stats frame
        stats_frame = ctk.CTkFrame(nutrition_frame)
        stats_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        
        ctk.CTkLabel(
            stats_frame,
            text="⟨ NUTRITION STATS ⟩",
            font=("Arial", 16, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).pack(pady=(15, 10))
        
        self.nutrition_stats_text = ctk.CTkTextbox(stats_frame, font=("Arial", 11))
        self.nutrition_stats_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
    
    def _create_summary_tab(self):
        """Summary tab"""
        summary_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(summary_frame, text="Summary Report")
        
        ctk.CTkLabel(
            summary_frame,
            text="⟨ PROGRESS SUMMARY ⟩",
            font=("Arial", 20, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).pack(pady=(20, 10))
        
        self.summary_text = ctk.CTkTextbox(summary_frame, font=("Arial", 12))
        self.summary_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    def _update_analysis(self, period):
        """Update all analysis based on selected period"""
        days = {"7 days": 7, "30 days": 30, "90 days": 90, "All time": 365}.get(period, 30)
        
        # Get data
        workout_data = self.data_manager.get_workout_data(days)
        nutrition_data = self.data_manager.get_nutrition_data(days)
        
        # Update each tab
        self._update_workout_analysis(workout_data)
        self._update_nutrition_analysis(nutrition_data)
        self._update_summary_report(workout_data, nutrition_data, period)
    
    def _update_workout_analysis(self, data):
        """Update workout analysis"""
        # Clear existing charts
        for widget in self.workout_charts_frame.winfo_children():
            widget.destroy()
        
        if data.empty:
            ctk.CTkLabel(
                self.workout_charts_frame,
                text="No workout data available\nfor the selected period.",
                font=("Arial", 16),
                text_color=AppColors.SECONDARY_TEXT
            ).pack(expand=True)
            
            self.workout_stats_text.delete("1.0", "end")
            self.workout_stats_text.insert("1.0", "No workout data to analyze.")
            return
        
        # Create matplotlib figure
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))
        fig.patch.set_facecolor(AppColors.CONCRETE_GRAY)
        
        # Volume over time
        daily_volume = data.groupby('Date').agg({'Weight': 'sum', 'Reps': 'sum'}).reset_index()
        daily_volume['Volume'] = daily_volume['Weight'] * daily_volume['Reps']
        
        ax1.plot(daily_volume['Date'], daily_volume['Volume'], color=AppColors.CROWN_GOLD, linewidth=2, marker='o')
        ax1.set_title('Total Volume Over Time', color=AppColors.PRIMARY_TEXT)
        ax1.set_facecolor(AppColors.CONCRETE_GRAY)
        ax1.tick_params(colors=AppColors.PRIMARY_TEXT)
        
        # Exercise frequency
        exercise_counts = data['Exercise'].value_counts().head(10)
        ax2.barh(exercise_counts.index, exercise_counts.values, color=AppColors.ELECTRIC_BLUE)
        ax2.set_title('Most Frequent Exercises', color=AppColors.PRIMARY_TEXT)
        ax2.set_facecolor(AppColors.CONCRETE_GRAY)
        ax2.tick_params(colors=AppColors.PRIMARY_TEXT)
        
        # RPE distribution
        if 'RPE' in data.columns and not data['RPE'].isna().all():
            rpe_counts = data['RPE'].value_counts().sort_index()
            ax3.bar(rpe_counts.index, rpe_counts.values, color=AppColors.FIRE_ORANGE)
            ax3.set_title('RPE Distribution', color=AppColors.PRIMARY_TEXT)
            ax3.set_xlabel('RPE', color=AppColors.PRIMARY_TEXT)
            ax3.set_facecolor(AppColors.CONCRETE_GRAY)
            ax3.tick_params(colors=AppColors.PRIMARY_TEXT)
        else:
            ax3.text(0.5, 0.5, 'No RPE data', transform=ax3.transAxes, ha='center', color=AppColors.SECONDARY_TEXT)
            ax3.set_facecolor(AppColors.CONCRETE_GRAY)
        
        # Workout frequency by goal
        if 'Goal' in data.columns:
            goal_counts = data.groupby('Goal').size()
            ax4.bar(goal_counts.index, goal_counts.values, color=AppColors.NEON_GREEN)
            ax4.set_title('Training by Goal', color=AppColors.PRIMARY_TEXT)
            ax4.set_facecolor(AppColors.CONCRETE_GRAY)
            ax4.tick_params(colors=AppColors.PRIMARY_TEXT)
            plt.setp(ax4.get_xticklabels(), rotation=45, ha='right')
        else:
            ax4.text(0.5, 0.5, 'No goal data', transform=ax4.transAxes, ha='center', color=AppColors.SECONDARY_TEXT)
            ax4.set_facecolor(AppColors.CONCRETE_GRAY)
        
        plt.tight_layout()
        
        # Add to tkinter
        canvas = FigureCanvasTkAgg(fig, self.workout_charts_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Update stats text
        total_workouts = len(data['Date'].unique())
        total_volume = (data['Weight'] * data['Reps']).sum()
        avg_rpe = data['RPE'].mean() if 'RPE' in data.columns else 0
        most_common_exercise = data['Exercise'].mode().iloc[0] if not data.empty else "N/A"
        
        stats_text = f"WORKOUT STATISTICS\n"
        stats_text += f"=" * 20 + "\n\n"
        stats_text += f"Total Workouts: {total_workouts}\n\n"
        stats_text += f"Total Volume: {total_volume:,.0f} lbs\n\n"
        stats_text += f"Average RPE: {avg_rpe:.1f}/10\n\n"
        stats_text += f"Most Common Exercise:\n{most_common_exercise}\n\n"
        stats_text += f"Workout Frequency:\n{total_workouts/4:.1f} per week\n\n"
        
        # Goal distribution
        if 'Goal' in data.columns:
            goal_counts = data['Goal'].value_counts()
            stats_text += f"TRAINING GOALS:\n"
            for goal, count in goal_counts.items():
                stats_text += f"• {goal}: {count} sessions\n"
            stats_text += "\n"
        
        if self.user_profile.get('mode') == 'Heavy Duty':
            recovery_hours = MentzerProtocols.RECOVERY_HOURS.get(self.user_profile.get('experience_level', 'Beginner'), 72)
            stats_text += f"HEAVY DUTY ANALYSIS:\n"
            stats_text += f"Recommended: {recovery_hours}+ hours\n"
            stats_text += f"Your Frequency: {(7*24)//(total_workouts/4) if total_workouts > 0 else 0} hours avg\n\n"
            
            if total_workouts/4 > 1.5:
                stats_text += "⚠️ Consider longer rest\nperiods for better recovery"
            else:
                stats_text += "✅ Good recovery timing"
        
        self.workout_stats_text.delete("1.0", "end")
        self.workout_stats_text.insert("1.0", stats_text)
    
    def _update_nutrition_analysis(self, data):
        """Update nutrition analysis"""
        # Clear existing charts
        for widget in self.nutrition_charts_frame.winfo_children():
            widget.destroy()
        
        if data.empty:
            ctk.CTkLabel(
                self.nutrition_charts_frame,
                text="No nutrition data available\nfor the selected period.",
                font=("Arial", 16),
                text_color=AppColors.SECONDARY_TEXT
            ).pack(expand=True)
            
            self.nutrition_stats_text.delete("1.0", "end")
            self.nutrition_stats_text.insert("1.0", "No nutrition data to analyze.")
            return
        
        # Create matplotlib figure
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))
        fig.patch.set_facecolor(AppColors.CONCRETE_GRAY)
        
        # Daily calories
        daily_cals = data.groupby('Date')['Calories'].sum().reset_index()
        ax1.plot(daily_cals['Date'], daily_cals['Calories'], color=AppColors.CROWN_GOLD, linewidth=2, marker='o')
        ax1.set_title('Daily Calories', color=AppColors.PRIMARY_TEXT)
        ax1.set_facecolor(AppColors.CONCRETE_GRAY)
        ax1.tick_params(colors=AppColors.PRIMARY_TEXT)
        
        # Macro distribution (pie chart)
        total_protein_cals = data['Protein'].sum() * 4
        total_carb_cals = data['Carbs'].sum() * 4
        total_fat_cals = data['Fat'].sum() * 9
        
        if total_protein_cals + total_carb_cals + total_fat_cals > 0:
            macro_data = [total_carb_cals, total_protein_cals, total_fat_cals]
            labels = ['Carbs', 'Protein', 'Fat']
            colors = [AppColors.ELECTRIC_BLUE, AppColors.NEON_GREEN, AppColors.FIRE_ORANGE]
            
            ax2.pie(macro_data, labels=labels, colors=colors, autopct='%1.1f%%', textprops={'color': AppColors.PRIMARY_TEXT})
            ax2.set_title('Macro Distribution', color=AppColors.PRIMARY_TEXT)
            ax2.set_facecolor(AppColors.CONCRETE_GRAY)
        
        # Top foods
        top_foods = data.groupby('Food')['Calories'].sum().sort_values(ascending=False).head(10)
        if not top_foods.empty:
            ax3.barh(range(len(top_foods)), top_foods.values, color=AppColors.CROWN_GOLD)
            ax3.set_yticks(range(len(top_foods)))
            ax3.set_yticklabels(top_foods.index, color=AppColors.PRIMARY_TEXT)
            ax3.set_title('Top Foods by Calories', color=AppColors.PRIMARY_TEXT)
            ax3.set_facecolor(AppColors.CONCRETE_GRAY)
            ax3.tick_params(colors=AppColors.PRIMARY_TEXT)
        
        # Meal distribution
        meal_cals = data.groupby('Meal_Type')['Calories'].sum()
        if not meal_cals.empty:
            ax4.bar(meal_cals.index, meal_cals.values, color=AppColors.ENERGY_RED)
            ax4.set_title('Calories by Meal Type', color=AppColors.PRIMARY_TEXT)
            ax4.set_facecolor(AppColors.CONCRETE_GRAY)
            ax4.tick_params(colors=AppColors.PRIMARY_TEXT)
            plt.setp(ax4.get_xticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Add to tkinter
        canvas = FigureCanvasTkAgg(fig, self.nutrition_charts_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Update stats text
        avg_calories = data.groupby('Date')['Calories'].sum().mean()
        avg_protein = data.groupby('Date')['Protein'].sum().mean()
        avg_carbs = data.groupby('Date')['Carbs'].sum().mean()
        avg_fat = data.groupby('Date')['Fat'].sum().mean()
        
        stats_text = f"NUTRITION STATISTICS\n"
        stats_text += f"=" * 20 + "\n\n"
        stats_text += f"Daily Averages:\n"
        stats_text += f"Calories: {avg_calories:.0f}\n"
        stats_text += f"Protein: {avg_protein:.1f}g\n"
        stats_text += f"Carbs: {avg_carbs:.1f}g\n"
        stats_text += f"Fat: {avg_fat:.1f}g\n\n"
        
        if self.user_profile.get('mode') == 'Heavy Duty':
            # Calculate actual ratios
            total_cals = avg_protein*4 + avg_carbs*4 + avg_fat*9
            if total_cals > 0:
                protein_ratio = (avg_protein * 4 / total_cals) * 100
                carb_ratio = (avg_carbs * 4 / total_cals) * 100
                fat_ratio = (avg_fat * 9 / total_cals) * 100
                
                stats_text += f"MENTZER'S 60/25/15:\n"
                stats_text += f"Your Ratios:\n"
                stats_text += f"Carbs: {carb_ratio:.1f}% (target 60%)\n"
                stats_text += f"Protein: {protein_ratio:.1f}% (target 25%)\n"
                stats_text += f"Fat: {fat_ratio:.1f}% (target 15%)\n\n"
                
                # Adherence assessment
                carb_diff = abs(carb_ratio - 60)
                protein_diff = abs(protein_ratio - 25)
                fat_diff = abs(fat_ratio - 15)
                
                if carb_diff < 5 and protein_diff < 5 and fat_diff < 5:
                    stats_text += "✅ Excellent adherence!"
                elif carb_diff < 10 and protein_diff < 10 and fat_diff < 10:
                    stats_text += "👍 Good adherence"
                else:
                    stats_text += "📈 Work on hitting ratios"
        
        self.nutrition_stats_text.delete("1.0", "end")
        self.nutrition_stats_text.insert("1.0", stats_text)
    
    def _update_summary_report(self, workout_data, nutrition_data, period):
        """Update summary report"""
        report_text = f"PROGRESS SUMMARY - {period.upper()}\n"
        report_text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report_text += f"User: {self.user_profile.get('mode', 'General')} Mode\n"
        report_text += "=" * 50 + "\n\n"
        
        # Workout Summary
        report_text += "TRAINING ANALYSIS:\n"
        report_text += "-" * 20 + "\n"
        
        if not workout_data.empty:
            total_workouts = len(workout_data['Date'].unique())
            total_volume = (workout_data['Weight'] * workout_data['Reps']).sum()
            unique_exercises = workout_data['Exercise'].nunique()
            avg_duration = workout_data['Duration'].mean() if 'Duration' in workout_data.columns else 0
            
            report_text += f"• Total Workouts: {total_workouts}\n"
            report_text += f"• Training Frequency: {total_workouts/(int(period.split()[0])/7):.1f} workouts/week\n"
            report_text += f"• Total Volume: {total_volume:,.0f} lbs\n"
            report_text += f"• Exercise Variety: {unique_exercises} different exercises\n"
            report_text += f"• Average Duration: {avg_duration:.0f} minutes\n"
            
            # Goal distribution
            if 'Goal' in workout_data.columns:
                goal_counts = workout_data['Goal'].value_counts()
                report_text += f"• Training Goals: {', '.join([f'{goal} ({count})' for goal, count in goal_counts.items()])}\n"
            
            # Heavy Duty specific analysis
            if self.user_profile.get('mode') == 'Heavy Duty':
                experience = self.user_profile.get('experience_level', 'Beginner')
                recommended_hours = MentzerProtocols.RECOVERY_HOURS.get(experience, 72)
                actual_frequency = total_workouts/(int(period.split()[0])/7)
                max_weekly_frequency = (7*24) / recommended_hours
                
                report_text += f"\nHEAVY DUTY COMPLIANCE:\n"
                report_text += f"• Experience Level: {experience}\n"
                report_text += f"• Recommended Recovery: {recommended_hours}+ hours\n"
                report_text += f"• Max Weekly Frequency: {max_weekly_frequency:.1f}\n"
                report_text += f"• Your Frequency: {actual_frequency:.1f}\n"
                
                if actual_frequency <= max_weekly_frequency:
                    report_text += f"✅ Excellent recovery compliance!\n"
                else:
                    report_text += f"⚠️ Consider longer rest periods\n"
        else:
            report_text += "No workout data for this period.\n"
        
        report_text += "\n"
        
        # Nutrition Summary
        report_text += "NUTRITION ANALYSIS:\n"
        report_text += "-" * 20 + "\n"
        
        if not nutrition_data.empty:
            daily_nutrition = nutrition_data.groupby('Date').agg({
                'Calories': 'sum',
                'Protein': 'sum',
                'Carbs': 'sum',
                'Fat': 'sum'
            })
            
            avg_calories = daily_nutrition['Calories'].mean()
            avg_protein = daily_nutrition['Protein'].mean()
            avg_carbs = daily_nutrition['Carbs'].mean()
            avg_fat = daily_nutrition['Fat'].mean()
            
            report_text += f"• Average Daily Calories: {avg_calories:.0f}\n"
            report_text += f"• Average Daily Protein: {avg_protein:.1f}g\n"
            report_text += f"• Average Daily Carbs: {avg_carbs:.1f}g\n"
            report_text += f"• Average Daily Fat: {avg_fat:.1f}g\n"
            
            # Macro ratios
            total_cals = avg_protein*4 + avg_carbs*4 + avg_fat*9
            if total_cals > 0:
                protein_ratio = (avg_protein * 4 / total_cals) * 100
                carb_ratio = (avg_carbs * 4 / total_cals) * 100
                fat_ratio = (avg_fat * 9 / total_cals) * 100
                
                report_text += f"\nMACRO RATIOS:\n"
                report_text += f"• Carbs: {carb_ratio:.1f}%"
                report_text += f" (target: 60%)" if self.user_profile.get('mode') == 'Heavy Duty' else ""
                report_text += f"\n• Protein: {protein_ratio:.1f}%"
                report_text += f" (target: 25%)" if self.user_profile.get('mode') == 'Heavy Duty' else ""
                report_text += f"\n• Fat: {fat_ratio:.1f}%"
                report_text += f" (target: 15%)" if self.user_profile.get('mode') == 'Heavy Duty' else ""
                report_text += "\n"
        else:
            report_text += "No nutrition data for this period.\n"
        
        # Overall Assessment
        report_text += "\nOVERALL ASSESSMENT:\n"
        report_text += "-" * 20 + "\n"
        
        if workout_data.empty and nutrition_data.empty:
            report_text += "No data available for analysis.\nStart logging workouts and nutrition to see progress!"
        elif workout_data.empty:
            report_text += "Good nutrition tracking! Add workout logging for complete analysis."
        elif nutrition_data.empty:
            report_text += "Great workout consistency! Add nutrition tracking to optimize results."
        else:
            report_text += "Excellent data tracking! You're on the path to achieving your goals.\n\n"
            
            if self.user_profile.get('mode') == 'Heavy Duty':
                report_text += 'Remember the key principle:\n'
                report_text += '"Recovery is when growth occurs."\n\n'
                report_text += "Continue following the brief, intense, infrequent approach\n"
                report_text += "for maximum natural bodybuilding results!"
        
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", report_text)

class PhilosophyWindow(ctk.CTkToplevel):
    """Mentzer's protocols and philosophy"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.title("gymratHD - Mentzer's Protocols")
        self.geometry("1000x700")
        self.configure(fg_color=AppColors.ELECTRIC_BLUE)
        
        self.transient(parent)
        self.grab_set()
        
        self._create_philosophy_interface()
    
    def _create_philosophy_interface(self):
        """Create philosophy interface"""
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            header_frame,
            text="⟨⟨⟨ MENTZER'S PROTOCOLS ⟩⟩⟩",
            font=("Arial", 24, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).pack(pady=20)
        
        ctk.CTkLabel(
            header_frame,
            text="Master the Science of High-Intensity Training",
            font=("Arial", 14),
            text_color=AppColors.PRIMARY_TEXT
        ).pack(pady=(0, 10))
        
        # Main content
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=2)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Left side - Topics
        topics_frame = ctk.CTkFrame(content_frame)
        topics_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        ctk.CTkLabel(
            topics_frame,
            text="⟨ TOPICS ⟩",
            font=("Arial", 16, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).pack(pady=(15, 10))
        
        topics = [
            ("Training Philosophy", self._show_philosophy),
            ("Recovery Science", self._show_recovery),
            ("Nutrition Protocols", self._show_nutrition),
            ("Exercise Selection", self._show_exercises),
            ("Intensity Techniques", self._show_intensity),
            ("Program Design", self._show_programs)
        ]
        
        for topic, command in topics:
            ctk.CTkButton(
                topics_frame,
                text=f"⟨ {topic} ⟩",
                command=command,
                fg_color=AppColors.CONCRETE_GRAY,
                text_color=AppColors.PRIMARY_TEXT,
                font=("Arial", 11),
                height=35
            ).pack(fill="x", padx=15, pady=3)
        
        # Right side - Content
        self.content_display = ctk.CTkTextbox(
            content_frame,
            font=("Arial", 12),
            text_color=AppColors.PRIMARY_TEXT
        )
        self.content_display.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        
        # Show initial content
        self._show_philosophy()
    
    def _show_philosophy(self):
        """Show training philosophy"""
        content = """TRAINING PHILOSOPHY

Mike Mentzer revolutionized bodybuilding by applying scientific principles to training. His Heavy Duty system is based on the understanding that muscle growth is an adaptation to stress, and that more stress is not necessarily better.

MENTZER'S KEY PRINCIPLES:

1. BRIEF WORKOUTS
• Workouts should last 30-45 minutes maximum
• Long workouts lead to overtraining and catabolism
• Quality over quantity in every exercise

2. INTENSE TRAINING
• Train to absolute muscular failure
• Use intensity techniques when appropriate
• Focus on progressive overload

3. INFREQUENT TRAINING
• Allow complete recovery between sessions
• Recovery is when growth actually occurs
• More frequent training interferes with adaptation

THE SCIENCE:
Muscle protein synthesis is elevated for 48-72 hours after intense training. Training again before full recovery impairs growth and leads to overtraining syndrome.

MENTZER'S INSIGHT:
"The workout doesn't produce growth - it merely triggers the mechanisms that produce growth during recovery."

This understanding led Mentzer to develop routines with very low volume but extremely high intensity, allowing for maximum recovery and growth.

PRACTICAL APPLICATION:
• Focus on compound movements
• Use perfect form
• Train each muscle group once every 4-7 days
• Prioritize sleep and nutrition during recovery periods

The Heavy Duty approach is particularly effective for natural bodybuilders who don't have the enhanced recovery capacity of enhanced athletes.

NOTE ON TRAINING GOALS:
While Mentzer focused primarily on hypertrophy (muscle growth), the app also includes general training parameters for Strength, Power, and Endurance goals. These are standard exercise science principles, not specific to Mentzer's teachings."""
        
        self.content_display.delete("1.0", "end")
        self.content_display.insert("1.0", content)
    
    def _show_recovery(self):
        """Show recovery science"""
        content = """RECOVERY SCIENCE

Recovery is the most misunderstood aspect of bodybuilding. Mentzer's revolutionary insight was that growth occurs during rest, not during the workout itself.

THE RECOVERY PROCESS:

1. IMMEDIATE RECOVERY (0-2 hours)
• Restoration of energy systems
• Clearing of metabolic byproducts
• Return to baseline homeostasis

2. ADAPTATION PHASE (24-72 hours)
• Muscle protein synthesis elevation
• Actual muscle tissue growth
• Strength increases occur here

3. SUPERCOMPENSATION (48-96 hours)
• Muscle is stronger than before training
• Optimal time for next workout
• Window varies by individual

MENTZER'S RECOVERY REQUIREMENTS BY EXPERIENCE:

BEGINNERS (0-6 months):
• 72+ hours between sessions
• Higher recovery capacity
• Can handle slightly more frequency

INTERMEDIATE (6 months - 2 years):
• 96+ hours between sessions
• Adaptation slows down
• Need more rest between workouts

ADVANCED (2+ years):
• 168+ hours (7+ days) between sessions
• Very efficient at muscle stimulation
• Require maximum recovery time

FACTORS AFFECTING RECOVERY:

POSITIVE FACTORS:
• Adequate sleep (8+ hours)
• Proper nutrition
• Stress management
• Hydration
• Age (younger recovers faster)

NEGATIVE FACTORS:
• Inadequate sleep
• Poor nutrition
• Life stress
• Other physical activities
• Age (older needs more time)

SIGNS OF INCOMPLETE RECOVERY:
• Decreased strength
• Lack of motivation to train
• Persistent muscle soreness
• Elevated resting heart rate
• Poor sleep quality

MENTZER'S RULE:
"When in doubt, rest another day. It's better to be undertrained than overtrained."

Remember: Your muscles don't grow in the gym - they grow in bed!"""
        
        self.content_display.delete("1.0", "end")
        self.content_display.insert("1.0", content)
    
    def _show_nutrition(self):
        """Show nutrition protocols"""
        content = """NUTRITION PROTOCOLS

Mentzer's approach to nutrition was as scientific as his training philosophy. He advocated for moderate protein intake and adequate carbohydrates to fuel high-intensity training.

MENTZER'S 60/25/15 PROTOCOL:

CARBOHYDRATES (60%):
• Primary fuel for intense training
• Necessary for muscle glycogen replenishment
• Support high-intensity efforts
• Don't fear carbs - they're muscle-sparing

PROTEIN (25%):
• Moderate intake, not excessive
• 1.0g per kg body weight maximum
• Quality over quantity
• Excess protein isn't used for muscle building

FAT (15%):
• Essential for hormone production
• Testosterone and growth hormone synthesis
• Fat-soluble vitamin absorption
• Cellular membrane integrity

WHY MODERATE PROTEIN?

Mentzer observed that excessive protein intake:
• Doesn't increase muscle growth beyond optimal levels
• Can be converted to glucose (gluconeogenesis)
• May stress the kidneys long-term
• Is often at the expense of energy-providing carbs

SCIENTIFIC SUPPORT:
Research consistently shows that protein needs for bodybuilders are much lower than commonly believed. Studies indicate 0.8-1.2g per kg body weight is sufficient for maximum muscle protein synthesis.

TIMING CONSIDERATIONS:
• Post-workout: Consume carbs and protein within 2 hours
• Pre-workout: Light carbs 1-2 hours before training
• Daily: Spread protein intake throughout the day
• Sleep: Light meal 2-3 hours before bed

PHASE-SPECIFIC ADJUSTMENTS:

MAINTENANCE:
• TDEE × 1.0
• Maintain body composition
• Standard 60/25/15 ratios

MUSCLE BUILDING:
• TDEE × 1.15
• Slight caloric surplus
• Maintain macro ratios

FAT LOSS:
• TDEE × 0.85
• Moderate deficit
• May increase protein slightly to preserve muscle

HYDRATION:
• 35ml per kg body weight minimum
• More during training days
• Clear urine is the goal

MENTZER'S PHILOSOPHY:
"Nutrition should support training, not complicate it. Keep it simple, keep it consistent, and focus on whole foods."""
        
        self.content_display.delete("1.0", "end")
        self.content_display.insert("1.0", content)
    
    def _show_exercises(self):
        """Show exercise selection"""
        content = """EXERCISE SELECTION

Mentzer prioritized compound movements that work multiple muscle groups simultaneously, providing maximum stimulation with minimum time investment.

MENTZER'S COMPOUND MOVEMENT HIERARCHY:

TIER 1 - ESSENTIAL EXERCISES:
• Squats - Ultimate lower body exercise
• Deadlifts - Total body power movement
• Pull-ups/Chin-ups - Best back builder
• Dips - Superior chest and tricep developer
• Overhead Press - Complete shoulder development

TIER 2 - SUPPORTING EXERCISES:
• Rows - Back thickness and detail
• Incline Press - Upper chest emphasis
• Close-Grip Press - Tricep specialization
• Barbell Curls - Bicep development

TIER 3 - ISOLATION (SPARINGLY):
• Lateral Raises - Medial deltoid isolation
• Calf Raises - Lower leg development
• Tricep Extensions - Tricep peak
• Leg Curls - Hamstring isolation

MENTZER'S PRE-EXHAUSTION TECHNIQUE:

This is Mentzer's signature method for maximizing muscle stimulation:

CHEST PRE-EXHAUSTION:
1. Dumbbell Flyes (isolation to failure)
2. Immediately perform Dumbbell Press (compound)
Result: Chest fails before triceps, ensuring complete chest stimulation

BACK PRE-EXHAUSTION:
1. Dumbbell Pullovers (lat isolation)
2. Immediately perform Pull-ups or Rows
Result: Lats fail before biceps

SHOULDER PRE-EXHAUSTION:
1. Lateral Raises (delt isolation)
2. Immediately perform Shoulder Press
Result: Deltoids fail before triceps

LEG PRE-EXHAUSTION:
1. Leg Extensions (quad isolation)
2. Immediately perform Squats
Result: Quads fail before lower back

MENTZER'S EXERCISE FORM PRINCIPLES:

1. CONTROLLED TEMPO:
• 2-4 seconds up (concentric)
• 1-2 second pause
• 4-6 seconds down (eccentric)

2. FULL RANGE OF MOTION:
• Complete stretch at bottom
• Full contraction at top
• No partial reps

3. CONTINUOUS TENSION:
• No rest at top or bottom
• Constant muscle tension
• No momentum or bouncing

4. MIND-MUSCLE CONNECTION:
• Focus on target muscle
• Feel every rep
• Quality over weight

EQUIPMENT CONSIDERATIONS:

DUMBBELLS:
• Allow full range of motion
• Unilateral training prevents imbalances
• Safer for solo training
• Perfect for home gyms

BARBELLS:
• Allow heavier loads
• Bilateral stability
• Progressive overload friendly
• Compound movement emphasis

MACHINES:
• Isolation capabilities
• Safety for beginners
• Consistent resistance curve
• Good for pre-exhaustion

Mentzer's preference was always for free weights when possible, as they recruit stabilizing muscles and provide the most natural movement patterns."""
        
        self.content_display.delete("1.0", "end")
        self.content_display.insert("1.0", content)
    
    def _show_intensity(self):
        """Show intensity techniques"""
        content = """INTENSITY TECHNIQUES

Mentzer developed and popularized several techniques to push muscles beyond normal failure points, ensuring maximum stimulation for growth.

1. TRAINING TO FAILURE

CONCENTRIC FAILURE:
• Unable to complete another full repetition
• The minimum requirement for growth stimulation
• Must be reached on every working set

IMPORTANCE:
• Recruits maximum motor units
• Triggers growth mechanisms
• Ensures progressive overload

TECHNIQUE:
• Use perfect form until failure
• No cheating or momentum
• Stop when form breaks down

2. FORCED REPS

DEFINITION:
• Partner assists with 2-3 additional reps after failure
• You provide as much force as possible
• Partner provides just enough help to complete rep

APPLICATION:
• Only on final set
• Maximum 2-3 forced reps
• Requires competent training partner

BENEFITS:
• Extends set beyond normal failure
• Increases time under tension
• Maximum muscle fiber recruitment

3. REST-PAUSE

TECHNIQUE:
• Train to failure
• Rest 10-15 seconds
• Perform additional reps to failure
• Repeat 2-3 times if desired

ADVANTAGE:
• No training partner required
• Allows brief energy system recovery
• Extends effective set duration

BEST USED ON:
• Isolation exercises
• Final working set
• When training alone

4. NEGATIVE EMPHASIS

TECHNIQUE:
• Use 10-20% more weight than normal
• Partner helps with concentric (lifting) phase
• You control eccentric (lowering) phase for 6-8 seconds
• Continue until can't control descent

SCIENCE:
• Eccentric contractions produce 40% more force
• Greater muscle damage (growth stimulus)
• Superior strength gains

APPLICATION:
• Sparingly - very demanding on recovery
• Final exercise of workout
• Requires experienced partner

5. PRE-EXHAUSTION

Already covered in exercise selection, but worth emphasizing:

PURPOSE:
• Ensure target muscle fails before assistance muscles
• Maximize stimulation of intended muscle group
• Overcome weak link problem

EXECUTION:
• Isolation exercise to failure
• Immediately perform compound exercise
• No rest between exercises

6. INFITONIC TRAINING

DEFINITION:
• Static contraction at point of maximum leverage
• Hold maximum contraction for 8-12 seconds
• Can be done at various joint angles

BENEFITS:
• Recruits maximum muscle fibers
• Builds incredible strength
• Time-efficient

APPLICATION:
• Can replace traditional reps
• Good for strength plateaus
• Useful when injured

MENTZER'S INTENSITY TECHNIQUE GUIDELINES:

FREQUENCY:
• Not every workout
• Only when feeling strong
• Listen to your body

RECOVERY:
• Require extra rest
• Monitor for overtraining signs
• Less frequent training

SELECTION:
• Choose technique that matches exercise
• Consider available equipment/partner
• Rotate techniques periodically

WARNING SIGNS:
• Decreased strength
• Loss of enthusiasm
• Persistent fatigue
• Joint pain

Remember: These techniques are tools, not requirements. Many champions built incredible physiques with basic training to failure."""
        
        self.content_display.delete("1.0", "end")
        self.content_display.insert("1.0", content)
    
    def _show_programs(self):
        """Show program design"""
        content = """PROGRAM DESIGN

Mentzer's approach to program design evolved throughout his career, ultimately arriving at extremely low-volume, high-intensity routines with long recovery periods.

MENTZER'S PROGRAM EVOLUTION:

EARLY HEAVY DUTY (1970s):
• 3 days per week
• Push/Pull/Legs split
• Higher volume than later programs
• Still emphasized intensity

MATURE HEAVY DUTY (1980s):
• 2 days per week
• Every 4th or 5th day training
• Consolidated routines
• Maximum intensity focus

FINAL EVOLUTION (1990s):
• Once every 7-10 days
• Single workout hitting all major muscles
• Ultra-brief sessions
• Perfect for advanced trainees

MENTZER'S CONSOLIDATION ROUTINE (Final Version):

WORKOUT A:
1. Squats - 1 set, 8-15 reps to failure
2. Close-Grip Pulldowns - 1 set, 6-10 reps to failure

WORKOUT B (7+ days later):
1. Deadlifts - 1 set, 6-10 reps to failure
2. Dips - 1 set, 6-10 reps to failure

FREQUENCY:
• Alternate A and B workouts
• 7-10 days between sessions
• Total body stimulation
• Minimum time commitment

MENTZER'S PROGRAM DESIGN PRINCIPLES:

1. EXERCISE SELECTION:
• Compound movements priority
• Multiple muscle stimulation
• Maximum bang for buck
• Minimize total exercises

2. VOLUME CONSIDERATIONS:
• Start with more, reduce as needed
• Advanced trainees need less volume
• Quality over quantity always
• Monitor recovery carefully

3. FREQUENCY PLANNING:
• Begin with higher frequency
• Reduce as intensity increases
• Listen to body's feedback
• Recovery is non-negotiable

4. PROGRESSION METHODS:
• Weight increases when possible
• Rep increases within range
• Time under tension
• Intensity techniques (sparingly)

MENTZER'S BEGINNER PROGRAM EXAMPLE:

WEEK 1-4:
Day 1: Chest, Back, Shoulders
Day 3: Legs, Arms
Day 6: Repeat

WEEK 5-12:
Day 1: Push muscles
Day 4: Pull muscles
Day 7: Legs

WEEK 13+:
Day 1: Full body
Day 5: Full body (different exercises)

PROGRAM MONITORING:

POSITIVE SIGNS:
• Strength increases
• Muscle growth
• High motivation
• Good sleep
• Looking forward to workouts

WARNING SIGNS:
• Strength plateaus or decreases
• Loss of muscle mass
• No motivation to train
• Poor sleep
• Dreading workouts

ADJUSTMENTS:
• Reduce volume before reducing intensity
• Add rest days
• Simplify exercises
• Check nutrition and sleep

MENTZER'S FINAL WISDOM:
"The perfect program is the one that provides maximum results with minimum time investment while allowing complete recovery."

Remember: These programs are guidelines. Individual response varies, and you must adjust based on your recovery capacity and progress.

NOTE: The app includes training parameters for various goals (Strength, Power, Endurance) based on general exercise science principles, which complement but are separate from Mentzer's specific Heavy Duty methodology focused on hypertrophy."""
        
        self.content_display.delete("1.0", "end")
        self.content_display.insert("1.0", content)

class GymratHD(ctk.CTk):
    """The complete gymratHD application"""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("gymratHD - The Ultimate Mike Mentzer Training & Nutrition Tracker")
        self.geometry("1600x1000")
        self.minsize(1400, 900)
        
        # Initialize systems
        self.data_manager = DataManager()
        self.user_profile = self.data_manager.load_user_profile()
        self.protocols = MentzerProtocols()
        self.food_database = self._load_food_database()
        
        # Show main interface
        self._create_main_interface()
        self._calculate_nutrition_targets()
        
        print("✅ gymratHD launched successfully!")
    
    def _load_food_database(self) -> Dict:
        """Load food database"""
        try:
            with open('food_database.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            # Fallback database
            return {
                "High-Protein Foods": {
                    "Chicken Breast": {"protein": 0.31, "carbs": 0.0, "fat": 0.036, "calories": 1.65},
                    "Greek Yogurt": {"protein": 0.17, "carbs": 0.095, "fat": 0.05, "calories": 1.3},
                    "Eggs": {"protein": 0.13, "carbs": 0.011, "fat": 0.11, "calories": 1.55}
                }
            }
    
    def _create_main_interface(self):
        """Create main interface"""
        # Configure main grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Create sections
        self._create_header()
        self._create_sidebar()
        self._create_main_content()
        self._create_footer()
    
    def _create_header(self):
        """Create header"""
        header_frame = ctk.CTkFrame(self, height=80)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # App title
        title_label = ctk.CTkLabel(
            header_frame,
            text="⟨⟨⟨ GYMRATHD ⟩⟩⟩",
            font=("Arial", 24, "bold"),
            text_color=AppColors.CROWN_GOLD
        )
        title_label.grid(row=0, column=0, padx=20, pady=20)
        
        # Mentzer quote - centered
        quote_label = ctk.CTkLabel(
            header_frame,
            text='"Recovery is when growth occurs." - Mike Mentzer',
            font=("Arial", 12, "italic"),
            text_color=AppColors.CROWN_GOLD
        )
        quote_label.grid(row=0, column=1, pady=20)
    
    def _create_sidebar(self):
        """Create sidebar"""
        sidebar_frame = ctk.CTkFrame(self, width=300)
        sidebar_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=5)
        sidebar_frame.grid_propagate(False)
        sidebar_frame.grid_columnconfigure(0, weight=1)
        
        # Profile section
        self._create_profile_section(sidebar_frame)
        
        # Quick actions
        self._create_quick_actions(sidebar_frame)
        
        # Nutrition display
        self._create_nutrition_display(sidebar_frame)
    
    def _create_profile_section(self, parent):
        """Profile section"""
        profile_frame = ctk.CTkFrame(parent)
        profile_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        profile_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            profile_frame,
            text="⟨ USER PROFILE ⟩",
            font=("Arial", 14, "bold"),
            text_color=AppColors.CROWN_GOLD
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(15, 20))
        
        # Profile fields
        row = 1
        
        # Weight
        ctk.CTkLabel(profile_frame, text="Weight (kg):", text_color=AppColors.CROWN_GOLD).grid(row=row, column=0, sticky="w", padx=15, pady=5)
        self.weight_var = tk.StringVar(value=str(self.user_profile['weight']))
        ctk.CTkEntry(profile_frame, textvariable=self.weight_var, width=100).grid(row=row, column=1, sticky="ew", padx=15, pady=5)
        row += 1
        
        # Height
        ctk.CTkLabel(profile_frame, text="Height (cm):", text_color=AppColors.CROWN_GOLD).grid(row=row, column=0, sticky="w", padx=15, pady=5)
        self.height_var = tk.StringVar(value=str(self.user_profile['height']))
        ctk.CTkEntry(profile_frame, textvariable=self.height_var, width=100).grid(row=row, column=1, sticky="ew", padx=15, pady=5)
        row += 1
        
        # Age
        ctk.CTkLabel(profile_frame, text="Age:", text_color=AppColors.CROWN_GOLD).grid(row=row, column=0, sticky="w", padx=15, pady=5)
        self.age_var = tk.StringVar(value=str(self.user_profile['age']))
        ctk.CTkEntry(profile_frame, textvariable=self.age_var, width=100).grid(row=row, column=1, sticky="ew", padx=15, pady=5)
        row += 1
        
        # Gender
        ctk.CTkLabel(profile_frame, text="Gender:", text_color=AppColors.CROWN_GOLD).grid(row=row, column=0, sticky="w", padx=15, pady=5)
        self.gender_var = tk.StringVar(value=self.user_profile['gender'])
        gender_menu = ctk.CTkOptionMenu(profile_frame, values=["Male", "Female"], variable=self.gender_var)
        gender_menu.grid(row=row, column=1, sticky="ew", padx=15, pady=5)
        row += 1
        
        # Activity Level
        ctk.CTkLabel(profile_frame, text="Activity:", text_color=AppColors.CROWN_GOLD).grid(row=row, column=0, sticky="w", padx=15, pady=5)
        self.activity_var = tk.StringVar(value=self.user_profile['activity_level'])
        activity_menu = ctk.CTkOptionMenu(profile_frame, values=["Sedentary", "Light", "Moderate", "Very Active"], variable=self.activity_var)
        activity_menu.grid(row=row, column=1, sticky="ew", padx=15, pady=5)
        row += 1
        
        # Training Goals
        ctk.CTkLabel(profile_frame, text="Goals:", text_color=AppColors.CROWN_GOLD).grid(row=row, column=0, sticky="w", padx=15, pady=5)
        current_goals = self.user_profile.get('goals', ['Hypertrophy'])
        if isinstance(current_goals, list):
            current_goal = current_goals[0]
        else:
            current_goal = current_goals
        
        self.goals_var = tk.StringVar(value=current_goal)
        goals_menu = ctk.CTkOptionMenu(profile_frame, values=["Strength", "Hypertrophy", "Power", "Endurance"], variable=self.goals_var)
        goals_menu.grid(row=row, column=1, sticky="ew", padx=15, pady=5)
        row += 1
        
        # Update button
        update_button = ctk.CTkButton(
            profile_frame,
            text="⟨ UPDATE PROFILE ⟩",
            command=self._update_profile,
            fg_color=AppColors.NEON_GREEN,
            text_color=AppColors.DEEP_BLACK,
            font=("Arial", 12, "bold")
        )
        update_button.grid(row=row, column=0, columnspan=2, pady=15, padx=15, sticky="ew")
    
    def _create_quick_actions(self, parent):
        """Quick actions"""
        actions_frame = ctk.CTkFrame(parent)
        actions_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(
            actions_frame,
            text="⟨ QUICK ACTIONS ⟩",
            font=("Arial", 14, "bold"),
            text_color=AppColors.CROWN_GOLD
        )
        title_label.pack(pady=(15, 20))
        
        # Action buttons
        actions = [
            ("START WORKOUT", self._start_workout, AppColors.ENERGY_RED),
            ("LOG NUTRITION", self._log_nutrition, AppColors.CROWN_GOLD),
            ("VIEW PROGRESS", self._view_progress, AppColors.FIRE_ORANGE),
            ("MENTZER'S PROTOCOLS", self._show_protocols, AppColors.ELECTRIC_BLUE)
        ]
        
        for text, command, color in actions:
            button = ctk.CTkButton(
                actions_frame,
                text=f"⟨ {text} ⟩",
                command=command,
                fg_color=color,
                text_color=AppColors.DEEP_BLACK if color != AppColors.ENERGY_RED else AppColors.PRIMARY_TEXT,
                font=("Arial", 11, "bold"),
                height=35
            )
            button.pack(pady=5, padx=15, fill="x")
    
    def _create_nutrition_display(self, parent):
        """Nutrition display"""
        nutrition_frame = ctk.CTkFrame(parent)
        nutrition_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        # Title
        if self.user_profile['mode'] == 'Heavy Duty':
            title_text = "⟨ 60/25/15 TARGETS ⟩"
        else:
            title_text = "⟨ NUTRITION TARGETS ⟩"
        
        title_label = ctk.CTkLabel(
            nutrition_frame,
            text=title_text,
            font=("Arial", 14, "bold"),
            text_color=AppColors.CROWN_GOLD
        )
        title_label.pack(pady=(15, 10))
        
        # Targets display
        self.nutrition_display = ctk.CTkTextbox(
            nutrition_frame,
            height=150,
            font=("Arial", 11),
            text_color=AppColors.PRIMARY_TEXT
        )
        self.nutrition_display.pack(pady=(0, 15), padx=15, fill="both", expand=True)
    
    def _create_main_content(self):
        """Main content"""
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Main content
        content_label = ctk.CTkLabel(
            main_frame,
            text="🏋️ GYMRATHD - READY TO EXCEL!\n\n🧠 Mike Mentzer's Heavy Duty Principles\n\n" +
                 '"Recovery is when growth occurs."\n' +
                 '"Train briefly, intensely, infrequently."\n' +
                 '"More is not better. Better is better."\n\n' +
                 "✅ Authentic 60/25/15 nutrition ratios\n" +
                 "✅ Scientific recovery protocols\n" +
                 "✅ Real workout tracking with data storage\n" +
                 "✅ Complete nutrition logging system\n" +
                 "✅ Progress analysis with charts\n" +
                 "✅ Mentzer's protocols education\n\n" +
                 "🎯 Perfect for natural bodybuilders seeking\n" +
                 "maximum results with minimal time investment!\n\n" +
                 "🔬 Scientifically accurate protocols\n" +
                 "Ready to start your Heavy Duty journey?",
            font=("Arial", 16),
            text_color=AppColors.PRIMARY_TEXT,
            justify="center"
        )
        content_label.place(relx=0.5, rely=0.5, anchor="center")
    
    def _create_footer(self):
        """Footer"""
        footer_frame = ctk.CTkFrame(self, height=50)
        footer_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 10))
        footer_frame.grid_propagate(False)
        footer_frame.grid_columnconfigure(1, weight=1)
        
        # Status
        self.status_label = ctk.CTkLabel(
            footer_frame,
            text="✅ Ready to excel with authentic Mentzer principles",
            font=("Arial", 11),
            text_color=AppColors.NEON_GREEN
        )
        self.status_label.grid(row=0, column=0, padx=20, pady=15)
        
        # Attribution
        attribution_label = ctk.CTkLabel(
            footer_frame,
            text="Created by: github.com/barebonesjones",
            font=("Arial", 9),
            text_color=AppColors.SECONDARY_TEXT
        )
        attribution_label.grid(row=0, column=1, padx=20, pady=15, sticky="e")
    
    def _calculate_nutrition_targets(self):
        """Calculate and display nutrition targets"""
        try:
            weight = float(self.weight_var.get())
            height = float(self.height_var.get())
            age = int(self.age_var.get())
            
            # Calculate BMR
            if self.gender_var.get() == 'Male':
                bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
            else:
                bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
            
            # Calculate TDEE
            activity_multipliers = {'Sedentary': 1.2, 'Light': 1.375, 'Moderate': 1.55, 'Very Active': 1.725}
            tdee = bmr * activity_multipliers.get(self.activity_var.get(), 1.55)
            
            # Calculate using Mentzer protocols
            targets = self.protocols.calculate_nutrition(weight, tdee, self.user_profile['phase'])
            
            # Update display
            if self.user_profile['mode'] == 'Heavy Duty':
                display_text = f"""🧠 MENTZER'S 60/25/15

📊 Daily Targets:
Calories: {targets['calories']:,}
Carbs: {targets['carbs']}g (60%)
Protein: {targets['protein']}g (25%)
Fat: {targets['fat']}g (15%)

🔬 Scientific Notes:
• Protein ceiling: {weight:.0f}g
• High carbs for intensity
• Essential fats for hormones

💪 Perfect for naturals!"""
            else:
                display_text = f"""⚡ NUTRITION TARGETS

📊 Daily Targets:
Calories: {targets['calories']:,}
Carbs: {targets['carbs']}g
Protein: {targets['protein']}g
Fat: {targets['fat']}g

🎯 Goals: {self.user_profile.get('goals', 'Hypertrophy')}
Phase: {self.user_profile['phase']}"""
            
            self.nutrition_display.delete("1.0", "end")
            self.nutrition_display.insert("1.0", display_text)
            
        except ValueError:
            self.nutrition_display.delete("1.0", "end")
            self.nutrition_display.insert("1.0", "Update profile to calculate targets")
    
    def _update_profile(self):
        """Update user profile"""
        try:
            # Update profile data
            self.user_profile.update({
                'weight': float(self.weight_var.get()),
                'height': float(self.height_var.get()),
                'age': int(self.age_var.get()),
                'gender': self.gender_var.get(),
                'activity_level': self.activity_var.get(),
                'goals': [self.goals_var.get()]
            })
            
            # Save to file
            self.data_manager.save_user_profile(self.user_profile)
            
            # Recalculate nutrition
            self._calculate_nutrition_targets()
            
            self.status_label.configure(text="✅ Profile updated and saved successfully!")
            
        except ValueError:
            self.status_label.configure(text="❌ Please enter valid numbers")
        except Exception:
            self.status_label.configure(text="❌ Failed to save profile")
    
    def _start_workout(self):
        """Open workout tracking window"""
        WorkoutWindow(self, self.data_manager, self.user_profile)
        self.status_label.configure(text="🏋️ Workout tracking opened - log your session!")
    
    def _log_nutrition(self):
        """Open nutrition tracking window"""
        NutritionWindow(self, self.data_manager, self.user_profile, self.food_database)
        self.status_label.configure(text="🍎 Nutrition tracking opened - track your macros!")
    
    def _view_progress(self):
        """Open progress analysis window"""
        ProgressWindow(self, self.data_manager, self.user_profile)
        self.status_label.configure(text="📊 Progress analysis opened - view your gains!")
    
    def _show_protocols(self):
        """Open protocols window"""
        PhilosophyWindow(self)
        self.status_label.configure(text="🎓 Mentzer's Protocols opened - learn Heavy Duty science!")
    
    def on_closing(self):
        """Handle app closing"""
        try:
            self.user_profile.update({
                'weight': float(self.weight_var.get()),
                'height': float(self.height_var.get()),
                'age': int(self.age_var.get()),
                'gender': self.gender_var.get(),
                'activity_level': self.activity_var.get(),
                'goals': [self.goals_var.get()]
            })
            self.data_manager.save_user_profile(self.user_profile)
        except Exception:
            pass
        
        self.destroy()

def main():
    """Launch gymratHD"""
    try:
        app = GymratHD()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch gymratHD: {e}")

if __name__ == "__main__":
    main()