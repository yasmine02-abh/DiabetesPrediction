from django.db import models

class Utilisateur(models.Model):
    nom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mot_de_passe = models.CharField(max_length=100)

class DonneeSante(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    age = models.IntegerField()
    bmi = models.FloatField()
    

class Recommendation(models.Model):
    donnee = models.ForeignKey(DonneeSante, on_delete=models.CASCADE)
    texte = models.TextField()
