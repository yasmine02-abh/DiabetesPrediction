from django.db import models
from django.utils import timezone

class Utilisateur(models.Model):
    nom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mot_de_passe = models.CharField(max_length=100)

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