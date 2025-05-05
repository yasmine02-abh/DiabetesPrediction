from django.db import models
from django.utils import timezone

class Utilisateur(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    ACTIVITY_LEVEL_CHOICES = [
        ('sedentary', 'Sedentary (little to no physical activity)'),
        ('moderate', 'Moderately Active (moderate exercise or physical activity)'),
        ('active', 'Active (intense exercise or physical activity)'),
    ]

    nom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mot_de_passe = models.CharField(max_length=100)
    age = models.IntegerField(default=30)
    gender = models.CharField(
        max_length=6, 
        choices=GENDER_CHOICES, 
        default='M'  # Set default value to avoid issues when adding the field
    )
    activity_level = models.CharField(
        max_length=10, 
        choices=ACTIVITY_LEVEL_CHOICES, 
        default='sedentary'  # Default value added here
    )

class DonneeSante(models.Model):
    utilisateur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE)
    age = models.IntegerField(default=30)
    bmi = models.FloatField(default=25.0)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female')],
        default='Male'
    )
    hypertension = models.BooleanField(default=False)
    heart_disease = models.BooleanField(default=False)
    smoking_history = models.CharField(
        max_length=10,
        choices=[('never', 'Never'), ('ever', 'Ever')],
        default='never'
    )
    hba1c_level = models.FloatField(default=5.5)
    blood_glucose_level = models.IntegerField(default=100)
    date_prediction = models.DateTimeField(default=timezone.now)
    result = models.CharField(max_length=100, default='Pending')

    def __str__(self):
        return f"DonneeSante for {self.utilisateur.nom}"
    

class Recommendation(models.Model):
    donnee = models.ForeignKey(DonneeSante, on_delete=models.CASCADE)
    texte = models.TextField()

    def __str__(self):
        return f"Recommendation for {self.donnee.utilisateur.nom}"
    


######
class Aliment(models.Model):
    nom = models.CharField(max_length=100)
    calories = models.FloatField(help_text="Calories pour 100g")

    def __str__(self):
        return f"{self.nom} - {self.calories} kcal/100g"

class Consommation(models.Model):
    utilisateur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE)
    aliment = models.ForeignKey(Aliment, on_delete=models.CASCADE)
    quantite = models.FloatField(help_text="Quantité en grammes")
    date = models.DateField(auto_now_add=True)

    def calories_totales(self):
        return (self.quantite / 100) * self.aliment.calories