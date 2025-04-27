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

from .models import DonneeSante
from django.contrib.auth.decorators import login_required
from django.template.defaultfilters import json_script
import json
from django.http import JsonResponse

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
            return redirect('login')  

    return render(request, 'register.html')



def dashboard(request):
    return render(request, "dashboard.html")

def charts(request):
    # Get the utilisateur_id from the session
    utilisateur_id = request.session.get('utilisateur_id')
    
   
    if utilisateur_id is None:
        
        return redirect('login')  

    try:
        utilisateur = Utilisateur.objects.get(id=utilisateur_id)
    except Utilisateur.DoesNotExist:
       
        return redirect('login') 

    # Get all DonneeSante entries for this utilisateur, ordered by date
    donnees = DonneeSante.objects.filter(utilisateur=utilisateur).order_by('date_prediction')

    # Prepare data for charts
    dates = [donnee.date_prediction.strftime("%Y-%m-%d %H:%M") for donnee in donnees]
    bmi_values = [donnee.bmi for donnee in donnees]
    hba1c_values = [donnee.hba1c_level for donnee in donnees]
    glucose_values = [donnee.blood_glucose_level for donnee in donnees]

    # Get the most recent values (last entry in the dataset)
    recent_donnee = donnees.last() if donnees else None
    recent_bmi = recent_donnee.bmi if recent_donnee else None
    recent_hba1c = recent_donnee.hba1c_level if recent_donnee else None
    recent_glucose = recent_donnee.blood_glucose_level if recent_donnee else None

    # Send the recent values to the template along with other context
    context = {
        'dates': dates,
        'bmi_values': bmi_values,
        'hba1c_values': hba1c_values,
        'glucose_values': glucose_values,
        'recent_bmi': recent_bmi,
        'recent_hba1c': recent_hba1c,
        'recent_glucose': recent_glucose,
    }

    return render(request, 'charts.html', context)




def profile(request):
    user_id = request.session.get('utilisateur_id')
    if not user_id:
        return redirect('login')  
    
    utilisateur = Utilisateur.objects.get(id=user_id)

    if request.method == 'POST':
        # Retrieve updated data from the form
        updated_nom = request.POST.get('nom')
        updated_email = request.POST.get('email')
        updated_mot_de_passe = request.POST.get('mot_de_passe')
        confirm_mot_de_passe = request.POST.get('confirm_password')

        # Update the user's name and email
        utilisateur.nom = updated_nom
        utilisateur.email = updated_email

        # Check if password change is requested
        if updated_mot_de_passe:
            # If password and confirmation don't match, show error message
            if updated_mot_de_passe != confirm_mot_de_passe:
                messages.error(request, "Passwords do not match. Please try again.")
                return render(request, 'profile.html', {'utilisateur': utilisateur})
            
            # If passwords match, update the password
            utilisateur.mot_de_passe = updated_mot_de_passe
        
        # Save updated user data
        utilisateur.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('profile')  # Redirect to the same profile page after update

    return render(request, 'profile.html', {'utilisateur': utilisateur})




# Load the trained model and scaler
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "ml_model/diabetes_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "ml_model/scaler.pkl")

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)


@login_required
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
            gender_numeric = 0 if gender == "Male" else 1  # For prediction only
            smoking_mapping = {"never": 0, "ever": 1}
            smoking_numeric = smoking_mapping.get(smoking_history, np.nan)

            # Create feature array
            features = np.array([
                gender_numeric, age, hypertension, heart_disease,
                smoking_numeric, bmi, HbA1c_level, blood_glucose_level
            ]).reshape(1, -1)

            # Standardize input
            features_scaled = scaler.transform(features)

            # Make prediction
            prediction = model.predict(features_scaled)[0]

            # Result message
            result = "You have diabetes" if prediction == 1 else "You are free from diabetes"

            # Retrieve the utilisateur from session
            utilisateur_id = request.session.get('utilisateur_id')
            if utilisateur_id:
                utilisateur = Utilisateur.objects.get(id=utilisateur_id)
            else:
                result = "Error: User has no associated Utilisateur."
                return render(request, "predict.html", {"result": result})

            # Create a new DonneeSante entry
            DonneeSante.objects.create(
                utilisateur=utilisateur,
                gender=gender,
                age=age,
                hypertension=bool(hypertension),
                heart_disease=bool(heart_disease),
                smoking_history=smoking_history,
                bmi=bmi,
                hba1c_level=HbA1c_level,
                blood_glucose_level=blood_glucose_level,
                result=result
            )

        except Exception as e:
            result = f"Error: {str(e)}"

    return render(request, "predict.html", {"result": result})
