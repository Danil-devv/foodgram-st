from django.shortcuts import redirect
from .models import Recipe


def recipe_short_link_redirect(request, recipe_id):
    return redirect(f"/recipes/{recipe_id}/") \
        if (Recipe.objects.filter(id=recipe_id).exists()) \
        else redirect("/")
