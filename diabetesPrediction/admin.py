from django.contrib import admin
from .models import Utilisateur, DonneeSante, Recommendation

admin.site.register(Utilisateur)
admin.site.register(DonneeSante)
admin.site.register(Recommendation)
