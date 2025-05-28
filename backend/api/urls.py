from django.urls import include, path


urlpatterns = [
    path("", include("users.urls")),
    path("", include("ingredients.urls")),
    path("", include(("recipes.urls", "recipes"), namespace="recipes")),
    path("auth/", include("djoser.urls.authtoken")),
]
