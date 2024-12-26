from django.urls import path
from .views import (
    SignUpView, LoginView, SignoutView, AllUsersView,
    
    # Therapy
    
    CreateSessionView, TherapistProfileUpdateView, GetAllSessionsView, ManageSessionView, GetAllTherapistView,
    
    # Payment
    
    BlockchainPaymentView, GetAllPaymentsView
)

urlpatterns = [
    path("user/signup", SignUpView.as_view()),
    path("user/signin", LoginView.as_view()),
    path("user/signout", SignoutView.as_view()),
    path("user/all", AllUsersView.as_view()),
    path("user/therapist/all", GetAllTherapistView.as_view()),
    path("user/therapist/profile/create/<int:id>", TherapistProfileUpdateView.as_view()),
    
    # Therapy
    path("therapy/session/create", CreateSessionView.as_view()),
    path("therapy/session/all", GetAllSessionsView.as_view()),
    path("therapy/session/update/<int:session_id>", ManageSessionView.as_view()),
    
    # Payment
    path("payment/session/create", BlockchainPaymentView.as_view()),
    path("payment/session/all", GetAllPaymentsView.as_view()),
]
