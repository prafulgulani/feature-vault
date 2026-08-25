from django.urls import path
from featurevault.views import user_feature_flags_view

app_name = "featurevault"

urlpatterns = [
    path("api/flags/", user_feature_flags_view, name="user_flags_api"),
]