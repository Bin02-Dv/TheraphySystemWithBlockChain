from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets
from rest_framework.views import APIView
from .models import Session, Payment, Therapist, AuthModel
from .serializers import SessionSerializer, PaymentSerializer, TherapistInFullSerializer, SessionInFullSerializer, PaymentInFullSerializer
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
import jwt
from datetime import datetime
from .blockChain import Blockchain
from rest_framework import status

from .serializers import (
    AuthModelSerializer
)

# Initialize blockchain
blockchain = Blockchain()

class SignUpView(APIView):
    def post(self, request):
        serializer = AuthModelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class LoginView(APIView):
    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        user = AuthModel.objects.filter(email=email).first()

        if user is None:
            raise AuthenticationFailed('Email NOT FOUND!!')
        
        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect Password!!')
        
        import datetime
        
        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, 'secret', algorithm='HS256')
        message = "Login success....."

        response = Response()

        response.set_cookie(key='jwt', value=token, httponly=True)

        response.data = {
            'jwt': token,
            'msg': message
        }
        
        return response

class AllUsersView(APIView):

    def get(self, request):
        users = AuthModel.objects.filter(role='user').order_by('-id')
        serializer = AuthModelSerializer(users, many=True)
        return Response(serializer.data)

class SignoutView(APIView):

    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            'message': 'Signout Successful..'
        }

        return response

class ActiveUserView(APIView):

    def get(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('User Unauthenticated!!')
        
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('User Unauthenticated!!')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        
        user = AuthModel.objects.filter(id=payload['id']).first()

        if not user:
            raise AuthenticationFailed('User not found')

        serializer = AuthModelSerializer(user)
        return Response(serializer.data)

class TherapistProfileUpdateView(APIView):
    
    def post(self, request, id):
    
        specialty = request.data.get("specialty")
        bio = request.data.get("bio")
        years_of_experience = request.data.get("years_of_experience")
        
        if not (id, specialty, bio, years_of_experience):
            return Response({"message": "All Fields (therapist, spaciality, bio, years of experience) Are Required!"}, status=status.HTTP_400_BAD_REQUEST)
        
        therapist = AuthModel.objects.get(id=id)
        
        Therapist.objects.create(
            user=therapist,
            specialty=specialty,
            bio=bio,
            years_of_experience=years_of_experience
        )
        
        therapist.role = "therapist"
        therapist.save()
        
        return Response({"message": "Profile create successfully.."}, status=status.HTTP_200_OK)
        

class BlockchainPaymentView(APIView):
    def post(self, request):
        # Step 1: Authenticate the User
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('User Unauthenticated!!')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('User Unauthenticated!!')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')

        user = AuthModel.objects.filter(id=payload['id']).first()
        if not user:
            raise AuthenticationFailed('User not found')

        # Step 2: Validate Request Data
        session_id = request.data.get('session')
        amount = request.data.get('amount')

        if not session_id or not amount:
            return Response({"error": "Session ID and amount are required"}, status=400)

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        session = Session.objects.filter(id=session_id).first()
        if not session:
            return Response({"error": "Session not found"}, status=404)

        # Step 3: Add Blockchain Transaction
        previous_block = blockchain.get_previous_block()
        proof = blockchain.proof_of_work(previous_block['proof'])
        previous_hash = blockchain.hash(previous_block)
        new_block = blockchain.create_block(proof, previous_hash)

        # Step 4: Save Payment in Database
        payment = Payment.objects.create(
            user=user,
            session=session,
            amount=amount,
            status='Paid'
        )

        # Step 5: Return Response
        return Response({
            "message": "Payment initiated successfully",
            "payment": PaymentSerializer(payment).data,
            "block": new_block
        })

class CreateSessionView(APIView):
    def post(self, request):
        # Step 1: Authenticate the User
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('User Unauthenticated!!')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('User Unauthenticated!!')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')

        user = AuthModel.objects.filter(id=payload['id']).first()
        if not user:
            raise AuthenticationFailed('User not found')

        # Step 2: Validate Session Data
        session_title = request.data.get('title')
        session_description = request.data.get('description')
        session_date = request.data.get('date')
        therapist_id = request.data.get('therapist')

        if not session_title or not session_date or not therapist_id:
            return Response({"error": "Title, date, and therapist ID are required"}, status=400)

        try:
            session_date = datetime.strptime(session_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        # Validate Therapist
        therapist = Therapist.objects.filter(id=therapist_id).first()
        if not therapist:
            return Response({"error": "Therapist not found"}, status=404)

        # Step 3: Add Blockchain Entry for the New Session
        previous_block = blockchain.get_previous_block()
        proof = blockchain.proof_of_work(previous_block['proof'])
        previous_hash = blockchain.hash(previous_block)
        new_block = blockchain.create_block(proof, previous_hash)

        # Step 4: Save Session in Database
        session = Session.objects.create(
            user=user,
            therapist=therapist,
            title=session_title,
            description=session_description,
            date=session_date,
            blockchain_reference=new_block['index']
        )

        # Step 5: Return Response
        return Response({
            "message": "Session created successfully",
            "session": SessionSerializer(session).data,
            "block": new_block
        })

class ManageSessionView(APIView):
    def put(self, request, session_id):
        # Step 1: Authenticate the Therapist
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Therapist Unauthenticated!!')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Therapist Unauthenticated!!')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')

        therapist_user = AuthModel.objects.filter(id=payload['id'], role='therapist').first()
        if not therapist_user:
            raise AuthenticationFailed('Only therapists can manage sessions')

        therapist = Therapist.objects.filter(user=therapist_user).first()
        if not therapist:
            return Response({"error": "Therapist profile not found"}, status=404)

        # Step 2: Find the Session
        session = Session.objects.filter(id=session_id, therapist=therapist).first()
        if not session:
            return Response({"error": "Session not found or unauthorized access"}, status=404)

        # Step 3: Approve or Reject the Session
        action = request.data.get('action')  # 'approve' or 'reject'
        if action == 'approve':
            session.status = 'Approved'
        elif action == 'reject':
            session.status = 'Rejected'
        else:
            return Response({"error": "Invalid action"}, status=400)

        # Step 4: Add Blockchain Transaction for Session Status Update
        previous_block = blockchain.get_previous_block()
        proof = blockchain.proof_of_work(previous_block['proof'])
        previous_hash = blockchain.hash(previous_block)
        new_block = blockchain.create_block(proof, previous_hash)

        # Step 5: Update Session with Blockchain Reference
        session.blockchain_reference = new_block['index']
        session.save()

        # Step 6: Return Response with Updated Session Data
        return Response({
            "message": f"Session {action}d successfully",
            "session": SessionSerializer(session).data,
            "block": new_block
        })

class GetAllSessionsView(APIView):
    def get(self, request):
        # Step 1: Authenticate the User
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('User Unauthenticated!!')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('User Unauthenticated!!')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')

        user = AuthModel.objects.filter(id=payload['id']).first()
        if not user:
            raise AuthenticationFailed('User not found')

        # Step 2: Retrieve Sessions Based on Role
        if user.role == 'user':
            # User's sessions
            sessions = Session.objects.filter(user=user)
        elif user.role == 'therapist':
            # Therapist's sessions
            therapist = Therapist.objects.filter(user=user).first()
            if not therapist:
                return Response({"error": "Therapist profile not found"}, status=404)
            sessions = Session.objects.filter(therapist=therapist)
        else:
            return Response({"error": "Invalid role"}, status=400)

        # Step 3: Serialize and Return the Data
        serializer = SessionInFullSerializer(sessions, many=True)
        return Response(serializer.data)
    
class GetAllPaymentsView(APIView):
    def get(self, request):
        # Step 1: Authenticate the User
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('User Unauthenticated!!')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('User Unauthenticated!!')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')

        user = AuthModel.objects.filter(id=payload['id']).first()
        if not user:
            raise AuthenticationFailed('User not found')

        # Step 2: Retrieve Payments Based on Role
        if user.role == 'user':
            # Payments related to the user
            payments = Payment.objects.filter(user=user)
        elif user.role == 'therapist':
            # Payments related to the therapist via sessions
            therapist = Therapist.objects.filter(user=user).first()
            if not therapist:
                return Response({"error": "Therapist profile not found"}, status=404)
            
            # Get sessions for the therapist
            sessions = Session.objects.filter(therapist=therapist)
            
            # Payments related to these sessions
            payments = Payment.objects.filter(session__in=sessions)
        else:
            return Response({"error": "Invalid role"}, status=400)

        # Step 3: Serialize and Return the Data
        serializer = PaymentInFullSerializer(payments, many=True)
        return Response(serializer.data)

class GetAllTherapistView(APIView):
    def get(self, request):
        # Step 1: Authenticate the User
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('User Unauthenticated!!')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('User Unauthenticated!!')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')

        user = AuthModel.objects.filter(id=payload['id']).first()
        if not user:
            raise AuthenticationFailed('User not found')

        # Step 2: Retrieve Sessions Based on Role
        if user.role == 'admin':
            # User's sessions
            therapist = Therapist.objects.all()
        else:
            return Response({"error": "You Don't have Access to this Information!!"}, status=400)

        # Step 3: Serialize and Return the Data
        serializer = TherapistInFullSerializer(therapist, many=True)
        return Response(serializer.data)