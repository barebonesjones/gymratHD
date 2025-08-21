"""
gymratHD - The Ultimate Mike Mentzer Training & Nutrition Tracker
================================================================================

Real workout tracking, real nutrition logging, real progress analysis.
FIXED: MacBook food loading issue in nutrition window

Created by: github.com/barebonesjones
Fixed: 2025-08-21 - MacBook food loading bug resolved
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

class NutritionWindow(ctk.CTkToplevel):
    """Fixed nutrition tracking window - MacBook compatible"""
    
    def __init__(self, parent, data_manager, user_profile, food_database):
        super().__init__(parent)
        self.parent = parent
        self.data_manager = data_manager
        self.user_profile = user_profile
        
        # Clean the food database to handle any HTML entities
        self.food_database = self._clean_food_database(food_database)
        
        self.title("gymratHD - Nutrition Tracking (MacBook Fixed)")
        self.geometry("1000x700")
        self.configure(fg_color=AppColors.DEEP_BLACK)
        
        # Today's nutrition data
        self.daily_nutrition = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
        self.nutrition_targets = self._calculate_targets()
        
        self.transient(parent)
        self.grab_set()
        
        # Debug info
        categories = [k for k in self.food_database.keys() if isinstance(self.food_database[k], dict)]
        print(f"DEBUG: Food database loaded with {len(categories)} categories")
        print(f"DEBUG: High-Protein Foods has {len(self.food_database.get('High-Protein Foods', {}))} items")
        
        self._create_nutrition_interface()
        self._load_todays_nutrition()
    
    def _clean_food_database(self, food_db):
        """Clean food database from any HTML entities"""
        def clean_text(text):
            if isinstance(text, str):
                return (text.replace('&amp;', '&')
                           .replace('&lt;', '<')
                           .replace('&gt;', '>')
                           .replace('&quot;', '"')
                           .replace('&#39;', "'"))
            return text
        
        cleaned_db = {}
        for key, value in food_db.items():
            clean_key = clean_text(key)
            if isinstance(value, dict):
                cleaned_value = {}
                for subkey, subvalue in value.items():
                    clean_subkey = clean_text(subkey)
                    cleaned_value[clean_subkey] = subvalue
                cleaned_db[clean_key] = cleaned_value
            else:
                cleaned_db[clean_key] = clean_text(value)
        return cleaned_db
    
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
            text="âŸ¨ NUTRITION TRACKING - MACBOOK FIXED âŸ©",
            font=("Arial", 18, "bold"),
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
        """Fixed food entry section"""
        entry_frame = ctk.CTkFrame(parent)
        entry_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        entry_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        ctk.CTkLabel(
            entry_frame,
            text="âŸ¨ ADD FOOD - MACBOOK FIXED âŸ©",
            font=("Arial", 16, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).grid(row=0, column=0, columnspan=2, pady=(15, 20))
        
        # Food selection
        ctk.CTkLabel(entry_frame, text="Food Category:", text_color=AppColors.CROWN_GOLD).grid(row=1, column=0, sticky="w", padx=15, pady=5)
        
        # Get food categories with error handling
        try:
            categories = [key for key in self.food_database.keys() if isinstance(self.food_database[key], dict)]
            print(f"DEBUG: Found {len(categories)} categories: {categories}")
            
            if not categories:
                categories = ["No categories available"]
        except Exception as e:
            print(f"ERROR: Failed to get categories: {e}")
            categories = ["Error loading categories"]
        
        self.category_var = tk.StringVar(value=categories[0] if categories else "")
        category_menu = ctk.CTkOptionMenu(
            entry_frame, 
            values=categories, 
            variable=self.category_var, 
            command=self._update_food_list_safe
        )
        category_menu.grid(row=1, column=1, sticky="ew", padx=15, pady=5)
        
        # Food item
        ctk.CTkLabel(entry_frame, text="Food Item:", text_color=AppColors.CROWN_GOLD).grid(row=2, column=0, sticky="w", padx=15, pady=5)
        
        self.food_var = tk.StringVar()
        # Start with loading message
        self.food_menu = ctk.CTkOptionMenu(entry_frame, values=["Loading..."], variable=self.food_var)
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
            text="âŸ¨ ADD FOOD âŸ©",
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
            text="âŸ¨ NUTRITION PREVIEW âŸ©",
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
        
        # Bind quantity change to update preview
        self.quantity_entry.bind('<KeyRelease>', self._update_preview)
        self.food_var.trace('w', lambda *args: self._update_preview())
        
        # Initialize food list after GUI is created (important for macOS)
        if categories and categories[0] not in ["No categories available", "Error loading categories"]:
            # Use after_idle to ensure proper initialization order
            print(f"DEBUG: Scheduling food list initialization for category: {categories[0]}")
            self.after_idle(lambda: self._update_food_list_safe(categories[0]))
        else:
            print("ERROR: Cannot initialize food list - no valid categories")
    
    def _update_food_list_safe(self, category):
        """Safe wrapper for food list update"""
        try:
            self._update_food_list(category)
        except Exception as e:
            print(f"ERROR in _update_food_list_safe: {e}")
            self.food_menu.configure(values=["Error loading foods"])
            self.food_var.set("Error loading foods")
    
    def _update_food_list(self, category):
        """Fixed food list update method"""
        try:
            print(f"DEBUG: Updating food list for category: '{category}'")
            
            if category not in self.food_database:
                print(f"ERROR: Category '{category}' not found")
                print(f"Available categories: {list(self.food_database.keys())}")
                return
            
            foods = list(self.food_database[category].keys())
            print(f"DEBUG: Found {len(foods)} foods in category '{category}'")
            
            if not foods:
                print(f"WARNING: No foods in category '{category}'")
                self.food_menu.configure(values=["No foods available"])
                return
            
            # Clear current selection first
            self.food_var.set("")
            
            # Try to update the food menu - this is where macOS issues occur
            try:
                # For macOS compatibility, limit to reasonable number of items
                original_count = len(foods)
                if len(foods) > 50:
                    foods = foods[:50]  # Limit to first 50 foods
                    print(f"DEBUG: Limited to first {len(foods)} foods (from {original_count}) for macOS compatibility")
                
                self.food_menu.configure(values=foods)
                print(f"DEBUG: Successfully updated food menu with {len(foods)} items")
                
                # Set first food as selected
                if foods:
                    self.food_var.set(foods[0])
                    print(f"DEBUG: Set selected food to '{foods[0]}'")
                    # Update preview after a short delay
                    self.after(100, self._update_preview)
                    
            except Exception as e:
                print(f"ERROR: Failed to update food menu: {e}")
                # Fallback - use only first 10 foods
                try:
                    fallback_foods = foods[:10]
                    self.food_menu.configure(values=fallback_foods)
                    if fallback_foods:
                        self.food_var.set(fallback_foods[0])
                    print(f"FALLBACK: Using first {len(fallback_foods)} foods")
                except Exception as e2:
                    print(f"CRITICAL ERROR: Even fallback failed: {e2}")
                    self.food_menu.configure(values=["Error loading foods"])
                    self.food_var.set("Error loading foods")
            
        except Exception as e:
            print(f"CRITICAL ERROR in _update_food_list: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_preview(self, event=None):
        """Update nutrition preview"""
        try:
            category = self.category_var.get()
            food = self.food_var.get()
            quantity = self.quantity_entry.get()
            
            if not all([category, food, quantity]) or food in ["Loading...", "Error loading foods", "No foods available"]:
                return
            
            try:
                quantity = float(quantity)
            except ValueError:
                self.preview_label.configure(text="Enter valid quantity")
                return
            
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
                
        except Exception as e:
            print(f"ERROR in _update_preview: {e}")
            self.preview_label.configure(text="Error calculating nutrition")
    
    def _add_food(self):
        """Add food to daily log"""
        try:
            category = self.category_var.get()
            food = self.food_var.get()
            quantity_str = self.quantity_entry.get()
            meal_type = self.meal_var.get()
            
            if not quantity_str:
                messagebox.showwarning("Missing Quantity", "Please enter a quantity in grams.")
                return
            
            try:
                quantity = float(quantity_str)
            except ValueError:
                messagebox.showerror("Invalid Quantity", "Please enter a valid quantity in grams.")
                return
            
            if not all([category, food]) or food in ["Loading...", "Error loading foods", "No foods available"]:
                messagebox.showwarning("Incomplete Data", "Please select a food category and item.")
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
                
        except Exception as e:
            print(f"ERROR in _add_food: {e}")
            messagebox.showerror("Error", f"Error adding food: {e}")
    
    def _create_daily_summary(self, parent):
        """Daily nutrition summary"""
        summary_frame = ctk.CTkFrame(parent)
        summary_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        
        # Title
        ctk.CTkLabel(
            summary_frame,
            text="âŸ¨ DAILY SUMMARY âŸ©",
            font=("Arial", 16, "bold"),
            text_color=AppColors.CROWN_GOLD
        ).pack(pady=(15, 10))
        
        # Targets vs actual
        self.summary_text = ctk.CTkTextbox(summary_frame, height=300, font=("Arial", 11))
        self.summary_text.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Update summary
        self._update_daily_summary()
    
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
        summary_text += f" {self.daily_nutrition['calories']:.0f} / {self.nutrition_targets['calories']:.0f} ({cal_percent:.1f}%)\n\n"
        
        summary_text += f"PROTEIN:\n"
        summary_text += f" {self.daily_nutrition['protein']:.1f}g / {self.nutrition_targets['protein']:.1f}g ({protein_percent:.1f}%)\n"
        if mode == 'Heavy Duty':
            summary_text += f" (25% of calories - moderate approach)\n\n"
        else:
            summary_text += "\n"
        
        summary_text += f"CARBS:\n"
        summary_text += f" {self.daily_nutrition['carbs']:.1f}g / {self.nutrition_targets['carbs']:.1f}g ({carbs_percent:.1f}%)\n"
        if mode == 'Heavy Duty':
            summary_text += f" (60% of calories - fuel for training)\n\n"
        else:
            summary_text += "\n"
        
        summary_text += f"FAT:\n"
        summary_text += f" {self.daily_nutrition['fat']:.1f}g / {self.nutrition_targets['fat']:.1f}g ({fat_percent:.1f}%)\n"
        if mode == 'Heavy Duty':
            summary_text += f" (15% of calories - hormonal support)\n\n"
        else:
            summary_text += "\n"
        
        # Overall status
        overall_percent = (cal_percent + protein_percent + carbs_percent + fat_percent) / 4
        if overall_percent >= 90:
            summary_text += "STATUS: Excellent adherence! ðŸŽ¯"
        elif overall_percent >= 70:
            summary_text += "STATUS: Good progress ðŸ‘"
        elif overall_percent >= 50:
            summary_text += "STATUS: Keep adding foods ðŸ“ˆ"
        else:
            summary_text += "STATUS: Just getting started ðŸš€"
        
        # Add debug info for troubleshooting
        categories = [k for k in self.food_database.keys() if isinstance(self.food_database[k], dict)]
        summary_text += f"\n\n[DEBUG] Categories: {len(categories)}"
        summary_text += f"\n[DEBUG] High-Protein: {len(self.food_database.get('High-Protein Foods', {}))}"
        
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", summary_text)
    
    def _load_todays_nutrition(self):
        """Load today's nutrition data"""
        try:
            today_data = self.data_manager.get_nutrition_data(days=1)
            today = datetime.now().strftime('%Y-%m-%d')
            today_foods = today_data[today_data['Date'].dt.strftime('%Y-%m-%d') == today]
            
            # Reset daily totals
            self.daily_nutrition = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
            
            # Add each food entry
            for _, food_entry in today_foods.iterrows():
                self.daily_nutrition['calories'] += food_entry['Calories']
                self.daily_nutrition['protein'] += food_entry['Protein']
                self.daily_nutrition['carbs'] += food_entry['Carbs']
                self.daily_nutrition['fat'] += food_entry['Fat']
            
            self._update_daily_summary()
            
        except Exception as e:
            print(f"Error loading today's nutrition: {e}")

# Minimal test application to verify the fix
class GymratHDMacBookTest(ctk.CTk):
    """Test application specifically for MacBook food loading issue"""
    
    def __init__(self):
        super().__init__()
        
        self.title("gymratHD MacBook Food Loading Test")
        self.geometry("800x600")
        
        # Load food database
        try:
            with open('food_database.json', 'r', encoding='utf-8') as f:
                self.food_database = json.load(f)
            print(f"Loaded food database with {len(self.food_database)} entries")
            
            # Count categories and high-protein foods
            categories = [k for k in self.food_database.keys() if isinstance(self.food_database[k], dict)]
            high_protein_count = len(self.food_database.get('High-Protein Foods', {}))
            print(f"Categories: {len(categories)}, High-Protein Foods: {high_protein_count}")
            
        except Exception as e:
            print(f"ERROR loading food database: {e}")
            self.food_database = {}
        
        # Create test interface
        self.create_test_interface()
    
    def create_test_interface(self):
        """Create test interface"""
        # Header
        header = ctk.CTkLabel(
            self, 
            text="âŸ¨ MACBOOK FOOD LOADING FIX TEST âŸ©",
            font=("Arial", 20, "bold"),
            text_color=AppColors.CROWN_GOLD
        )
        header.pack(pady=20)
        
        # Info
        info = ctk.CTkLabel(
            self,
            text="This version fixes the '3 foods only' issue on MacBook",
            font=("Arial", 12),
            text_color=AppColors.PRIMARY_TEXT
        )
        info.pack(pady=10)
        
        # Test button
        test_button = ctk.CTkButton(
            self,
            text="âŸ¨ TEST NUTRITION WINDOW âŸ©",
            command=self.test_nutrition_window,
            font=("Arial", 14, "bold"),
            height=40
        )
        test_button.pack(pady=20)
        
        # Status display
        self.status_text = ctk.CTkTextbox(self, height=350, font=("Arial", 11))
        self.status_text.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Initial status
        self.update_status("Ready to test MacBook food loading fix!")
        self.update_status(f"Food database loaded: {len(self.food_database)} entries")
        
        categories = [k for k in self.food_database.keys() if isinstance(self.food_database[k], dict)]
        self.update_status(f"Categories found: {len(categories)}")
        self.update_status(f"High-Protein Foods: {len(self.food_database.get('High-Protein Foods', {}))} items")
    
    def update_status(self, message):
        """Update status display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert("end", f"[{timestamp}] {message}\n")
        self.status_text.see("end")
        self.update()  # Force GUI update
    
    def test_nutrition_window(self):
        """Test the nutrition window with MacBook fixes"""
        self.update_status("Opening nutrition window with MacBook fixes...")
        
        try:
            # Create dummy data manager and user profile
            data_manager = DataManager()
            user_profile = {
                'weight': 75, 'height': 180, 'age': 30, 'gender': 'Male',
                'activity_level': 'Moderate', 'mode': 'Heavy Duty', 'phase': 'Maintenance'
            }
            
            self.update_status("Creating nutrition window...")
            
            # Open nutrition window with fixes
            nutrition_window = NutritionWindow(self, data_manager, user_profile, self.food_database)
            self.update_status("âœ… Nutrition window opened successfully!")
            self.update_status("Check if all high-protein foods are now visible!")
            
        except Exception as e:
            self.update_status(f"âŒ ERROR: Failed to open nutrition window: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("="*70)
    print("GYMRATHD MACBOOK FOOD LOADING FIX")
    print("="*70)
    print("This version specifically addresses the MacBook issue where")
    print("only 3 foods were showing in the High-Protein Foods category.")
    print()
    print("Key fixes applied:")
    print("- HTML entity cleaning in food database")
    print("- macOS CustomTkinter OptionMenu compatibility")
    print("- Limited food lists to 50 items max for stability")
    print("- Comprehensive error handling and debugging")
    print("- Proper GUI initialization timing with after_idle()")
    print("="*70)
    
    app = GymratHDMacBookTest()
    app.mainloop()