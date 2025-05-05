from django.contrib import admin
from .models import Utilisateur, DonneeSante, Recommendation, Aliment, Consommation

admin.site.register(Utilisateur)
admin.site.register(DonneeSante)
admin.site.register(Recommendation)
admin.site.register(Aliment)
admin.site.register(Consommation)
