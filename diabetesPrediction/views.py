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

from .models import Aliment, Consommation
from .utils import chercher_aliment

from django.db.models import F, Sum
from django.db.models.functions import TruncDate

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
        gender = request.POST.get('gender')
        activity_level = request.POST.get('activity_level')
        age = request.POST.get('age')

        if Utilisateur.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
        else:
            Utilisateur.objects.create(nom=nom, email=email, mot_de_passe=mot_de_passe, gender=gender, activity_level=activity_level, age=age)
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
        updated_age = request.POST.get('age')
        updated_gender = request.POST.get('gender')
        updated_activity_level = request.POST.get('activity_level')

        # Update the user's name and email
        utilisateur.nom = updated_nom
        utilisateur.email = updated_email

        if updated_age:
            utilisateur.age = int(updated_age)
        utilisateur.gender = updated_gender
        utilisateur.activity_level = updated_activity_level

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



def predict_diabetes(request):
    result = None
    utilisateur_id = request.session.get('utilisateur_id')  # Get the logged-in user ID from the session
    
    if utilisateur_id:
        try:
            # Retrieve the utilisateur (user) from the database
            utilisateur = Utilisateur.objects.get(id=utilisateur_id)
            gender = utilisateur.gender  # Assuming 'gender' is a field in the 'Utilisateur' model
            age = utilisateur.age  # Assuming 'age' is a field in the 'Utilisateur' model

            if gender == 'M':
                gender = 'Male'
            elif gender == 'F':
                gender = 'Female'
            
        except Utilisateur.DoesNotExist:
            result = "Error: User not found."
            return render(request, "predict.html", {"result": result})
    else:
        result = "Error: No user is logged in."
        return render(request, "predict.html", {"result": result})
    if request.method == "POST":
        try:
            
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

    return render(request, "predict.html", {"result": result, "gender": gender, "age": age})




#####
def rechercher_aliment(request):
    resultat = None
    message = None

    if request.method == 'POST':
        nom = request.POST.get('nom')
        if 'ajouter' in request.POST:
            # Check if the aliment already exists in the database (case-insensitive)
            if Aliment.objects.filter(nom__iexact=nom).exists():
                message = f"L'aliment '{nom}' existe déjà dans la base de données."
            else:
                # Ajouter à la base de données avec une valeur numérique propre (en kcal)
                Aliment.objects.create(
                    nom=nom,
                    calories=float(request.POST['calories'])  # en kcal
                )
                message = f"L'aliment '{nom}' a été ajouté avec succès."
        else:
            data = chercher_aliment(nom)
            if data:
                data['nom'] = nom
                # NE PAS multiplier par 1000, garder en kcal
                # arrondir à 2 chiffres après la virgule pour l'affichage
                data['calories'] = round(data['calories'], 2)
                resultat = data
            else:
                message = "Aucun aliment trouvé. Essayez un autre nom."

    return render(request, 'rechercher_aliment.html', {
        'resultat': resultat,
        'message': message
    })



def ajouter_consommation(request):
    message = None
    
    if request.method == 'POST':
        aliment_id = request.POST.get('aliment_id')
        quantite = float(request.POST.get('quantite'))
        
        # Vérifier si l'aliment existe dans la base de données
        aliment = Aliment.objects.get(id=aliment_id)
        
        # Récupérer l'utilisateur connecté depuis la session
        utilisateur_id = request.session.get('utilisateur_id')
        
        if utilisateur_id:
            # Utiliser le modèle Utilisateur pour récupérer l'utilisateur
            utilisateur = Utilisateur.objects.get(id=utilisateur_id)
        else:
            # Si l'utilisateur n'est pas trouvé dans la session, vous pouvez gérer l'erreur
            message = "Utilisateur non authentifié. Veuillez vous connecter."
            return redirect('login')  # Rediriger vers la page de connexion si nécessaire

        # Ajouter la consommation à la base de données
        Consommation.objects.create(
            utilisateur=utilisateur,
            aliment=aliment,
            quantite=quantite
        )
        
        message = f"{quantite}g de {aliment.nom} ont été ajoutés à votre consommation."

    # Afficher tous les aliments disponibles dans la base
    aliments = Aliment.objects.all()
    return render(request, 'ajouter_consommation.html', {'aliments': aliments, 'message': message})




def suivi_calories(request):
    utilisateur_id = request.session.get('utilisateur_id')
    if not utilisateur_id:
        return redirect('login')

    utilisateur = Utilisateur.objects.get(id=utilisateur_id)

    consommations = Consommation.objects.filter(utilisateur=utilisateur).order_by('-date')

    daily_calories = None
    if consommations.exists():
        latest_date = consommations.first().date  # Pas besoin de .date() si déjà DateField

        consommations_du_jour = consommations.filter(date=latest_date)  # ✅ Ici

        total_calories = sum(
            (c.aliment.calories * c.quantite) / 100 for c in consommations_du_jour
        )

        gender = utilisateur.gender
        age = utilisateur.age
        activity = utilisateur.activity_level

        if gender == "M":
            if 19 <= age <= 30:
                if activity == "sedentary":
                    daily_calories = 2400
                elif activity == "moderate":
                    daily_calories = 2600
                elif activity == "active":
                    daily_calories = 3000
            elif 31 <= age <= 50:
                if activity == "sedentary":
                    daily_calories = 2200
                elif activity == "moderate":
                    daily_calories = 2400
                elif activity == "active":
                    daily_calories = 2800
            else:
                if activity == "sedentary":
                    daily_calories = 2000
                elif activity == "moderate":
                    daily_calories = 2200
                elif activity == "active":
                    daily_calories = 2400

        elif gender == "F":
            if 19 <= age <= 30:
                if activity == "sedentary":
                    daily_calories = 1800
                elif activity == "moderate":
                    daily_calories = 2000
                elif activity == "active":
                    daily_calories = 2400
            elif 31 <= age <= 50:
                if activity == "sedentary":
                    daily_calories = 1800
                elif activity == "moderate":
                    daily_calories = 2000
                elif activity == "active":
                    daily_calories = 2200
            else:
                if activity == "sedentary":
                    daily_calories = 1600
                elif activity == "moderate":
                    daily_calories = 1800
                elif activity == "active":
                    daily_calories = 2000


        return render(request, 'suivi_calories.html', {
            'consommations': consommations_du_jour,
            'total_calories': total_calories,
            'date_jour': latest_date,
            'daily_calories': daily_calories,
        })

    return render(request, 'suivi_calories.html', {
        'consommations': [],
        'total_calories': 0,
        'daily_calories': None
    })


from collections import defaultdict
from decimal import Decimal

def graphe_calories(request):
    utilisateur_id = request.session.get('utilisateur_id')
    if not utilisateur_id:
        return redirect('login')

    utilisateur = Utilisateur.objects.get(id=utilisateur_id)

    consommations = (
        Consommation.objects
        .filter(utilisateur=utilisateur)
        .select_related('aliment')
        .order_by('date')
    )

    calories_par_jour = defaultdict(float)
    for conso in consommations:
        date_jour = conso.date
        if conso.aliment and conso.aliment.calories and conso.quantite:
            calories = (Decimal(conso.aliment.calories) * Decimal(conso.quantite)) / Decimal(100)
            calories_par_jour[date_jour] += float(calories)

    dates = [date.strftime('%Y-%m-%d') for date in sorted(calories_par_jour.keys())]
    calories = [calories_par_jour[date] for date in sorted(calories_par_jour.keys())]

    context = {
        'dates': dates,
        'calories': calories
    }
    return render(request, 'graphe_calories.html', context)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def advices_view(request):
    try:
        utilisateur_id = request.session.get('utilisateur_id')
        
        if not utilisateur_id:
            return redirect('login')  # Si l'ID de l'utilisateur est introuvable, rediriger vers le login

        utilisateur = Utilisateur.objects.get(id=utilisateur_id)
        
        # Récupérer la dernière entrée de DonneeSante pour l'utilisateur
        try:
            last_data = DonneeSante.objects.filter(utilisateur=utilisateur).latest('date_prediction')
        except DonneeSante.DoesNotExist:
            message = "No health data found. Please update your health data first."
            return render(request, 'advices.html', {'message': message})
        
        # Obtenir toutes les recommandations associées à cette donnée de santé
       # recommandations = Recommendation.objects.filter(donnee=last_data)
        
        # Message personnalisé
        if last_data.result:
            if last_data.result == "You have diabetes":
                message = "It seems you are diagnosed with diabetes. Here are some personalized recommendations for you!"
            else:
                message = "Bonne nouvelle ! Vous n'êtes pas à risque selon notre prédiction."
        else:
            message = "Health data is incomplete. Please update your information."
        
        # Passer les données au template
        context = {
            'message': message,
            #'recommandations': recommandations,
            'user': utilisateur,
            'last_data': last_data
        }
        return render(request, 'advices.html', context)
    
    except Utilisateur.DoesNotExist:
        # Si l'utilisateur n'existe pas, rediriger vers la page de connexion
        return redirect('login')

import requests
from django.shortcuts import render, redirect
from .models import DonneeSante, Utilisateur

def get_recipes_from_spoonacular(query="healthy", number=6):
    api_key = "f3fb07c5b6974a59a924321a01205260"  # 🔁 Remplace par ta vraie clé API
    url = "https://api.spoonacular.com/recipes/complexSearch"
    
    params = {
        "apiKey": api_key,
        "query": query,
        "number": number,
        "addRecipeInformation": True
    }

    response = requests.get(url, params=params)
  
    data = response.json()
    print("Raw API response:", data)
    
    results = []
    for item in data.get("results", []):
        results.append({
            "title": item["title"],
            "summary": item["summary"],
            "url": item["sourceUrl"],
            "image": item["image"]
        })
    
    return results

def recettes_view(request):
    try:
        utilisateur_id = request.session.get('utilisateur_id')
        
        if not utilisateur_id:
            return redirect('login')  # Utilisateur non connecté

        utilisateur = Utilisateur.objects.get(id=utilisateur_id)

        # Récupérer la dernière donnée de santé
        try:
            last_data = DonneeSante.objects.filter(utilisateur=utilisateur).latest('date_prediction')
        except DonneeSante.DoesNotExist:
            message = "Aucune donnée de santé trouvée. Veuillez les renseigner d'abord."
            return render(request, 'recettes.html', {'message': message})

        # Choix du type de recette selon les données santé
        if last_data.bmi > 30:
            recipes = get_recipes_from_spoonacular("healthy salad")
            
        elif last_data.hba1c_level > 6.5:
            recipes = get_recipes_from_spoonacular("no sugar meals")
           
        else:
            recipes = get_recipes_from_spoonacular("healthy high protein meals ")
            

        context = {
            'recipes': recipes,
            'last_data': last_data,
            'user': utilisateur
        }

        return render(request, 'recettes.html', context)

    except Utilisateur.DoesNotExist:
        return redirect('login')

