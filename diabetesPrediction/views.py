from django.shortcuts import render
import joblib
import numpy as np
import os
from django.shortcuts import render, redirect
from .models import Utilisateur

from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib import messages

def home(request):
    return render(request, "home.html")

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        mot_de_passe = request.POST.get('password')

        try:
            user = Utilisateur.objects.get(email=email)
            if user.mot_de_passe == mot_de_passe:  
                request.session['utilisateur_id'] = user.id  
                return redirect('dashboard')  
            else:
                messages.error(request, "Incorrect password.")
        except Utilisateur.DoesNotExist:
            messages.error(request, "No user found with this email.")

    return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        mot_de_passe = request.POST.get('password')

        if Utilisateur.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
        else:
            Utilisateur.objects.create(nom=nom, email=email, mot_de_passe=mot_de_passe)
            messages.success(request, "Account created successfully. You can now log in.")
            return redirect('login')  # Adjust based on your URL name

    return render(request, 'register.html')



def dashboard(request):
    return render(request, "dashboard.html")




# Load the trained model and scaler
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "ml_model/diabetes_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "ml_model/scaler.pkl")

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)


def predict_diabetes(request):
    result = None
    if request.method == "POST":
        try:
            # Get data from form
            gender = request.POST.get("gender")
            age = float(request.POST.get("age"))
            hypertension = int(request.POST.get("hypertension"))
            heart_disease = int(request.POST.get("heart_disease"))
            smoking_history = request.POST.get("smoking_history")
            bmi = float(request.POST.get("bmi"))
            HbA1c_level = float(request.POST.get("HbA1c_level"))
            blood_glucose_level = float(request.POST.get("blood_glucose_level"))

            # Convert gender & smoking history to numeric values
            gender = 0 if gender == "Male" else 1
            smoking_mapping = {"never": 0, "ever": 1}
            smoking_history = smoking_mapping.get(smoking_history, np.nan)

            # Create feature array
            features = np.array([
                gender, age, hypertension, heart_disease,
                smoking_history, bmi, HbA1c_level, blood_glucose_level
            ]).reshape(1, -1)

            # Standardize input
            features_scaled = scaler.transform(features)

            # Make prediction
            prediction = model.predict(features_scaled)[0]

            # Result message
            result = "You have diabetes" if prediction == 1 else "You are free from diabetes"

        except Exception as e:
            result = f"Error: {str(e)}"

    return render(request, "predict.html", {"result": result})

