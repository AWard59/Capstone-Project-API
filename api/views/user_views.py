from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework import status, generics
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user, authenticate, login, logout

from ..serializers import UserSerializer, UserRegisterSerializer, ChangePasswordSerializer, UpdateProfileSerializer, TutorSerializer
from ..models.user import User

class SignUpView(generics.CreateAPIView):
    # Override the authentication/permissions classes so this endpoint
    # is not authenticated & we don't need any permissions to access it.
    authentication_classes = ()
    permission_classes = ()

    # Serializer classes are required for endpoints that create data
    serializer_class = UserRegisterSerializer

    def post(self, request):
        # Pass the request data to the serializer to validate it
        if (request.data['userType'] == 'is_student'):
            request.data['credentials']['is_student'] = True
            request.data['credentials']['is_tutor'] = False
            request.data['credentials']['is_author'] = False
        elif (request.data['userType'] == 'is_tutor'):
            request.data['credentials']['is_tutor'] = True
            request.data['credentials']['is_student'] = False
            request.data['credentials']['is_author'] = False
        elif (request.data['userType'] == 'is_author'):
            request.data['credentials']['is_author'] = True
            request.data['credentials']['is_student'] = False
            request.data['credentials']['is_tutor'] = False

        user = UserRegisterSerializer(data=request.data['credentials'])
        # If that data is in the correct format...
        if user.is_valid():
            # Actually create the user using the UserSerializer (the `create` method defined there)
            created_user = UserSerializer(data=user.data)
            if created_user.is_valid():
                # Save the user and send back a response!
                created_user.save()
                return Response({ 'user': created_user.data }, status=status.HTTP_201_CREATED)
            else:
                return Response(created_user.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)

class SignInView(generics.CreateAPIView):
    # Override the authentication/permissions classes so this endpoint
    # is not authenticated & we don't need any permissions to access it.
    authentication_classes = ()
    permission_classes = ()

    # Serializer classes are required for endpoints that create data
    serializer_class = UserSerializer

    def post(self, request):
        creds = request.data['credentials']
        # We can pass our email and password along with the request to the
        # `authenticate` method. If we had used the default user, we would need
        # to send the `username` instead of `email`.
        user = authenticate(request, email=creds['email'], password=creds['password'])
        # Is our user is successfully authenticated...
        if user is not None:
            # And they're active...
            if user.is_active:
                # Log them in!
                login(request, user)
                # Finally, return a response with the user's token
                return Response({
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'token': user.get_auth_token(),
                        'isAuthor': user.is_author,
                        'isTutor': user.is_tutor,
                        'isStudent': user.is_student
                    }
                })
            else:
                return Response({ 'msg': 'The account is inactive.' }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({ 'msg': 'The username and/or password is incorrect.' }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

class SignOutView(generics.DestroyAPIView):
    def delete(self, request):
        # Remove this token from the user
        request.user.delete_token()
        # Logout will remove all session data
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ChangePasswordView(generics.UpdateAPIView):
    def partial_update(self, request):
        user = request.user
        # Pass data through serializer
        serializer = ChangePasswordSerializer(data=request.data['passwords'])
        if serializer.is_valid():
            # This is included with the Django base user model
            # https://docs.djangoproject.com/en/3.2/ref/contrib/auth/#django.contrib.auth.models.User.check_password
            if not user.check_password(serializer.data['old']):
                return Response({ 'msg': 'Wrong password' }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            # set_password will also hash the password
            # https://docs.djangoproject.com/en/3.2/ref/contrib/auth/#django.contrib.auth.models.User.set_password
            user.set_password(serializer.data['new'])
            user.save()

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateProfileView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    # def partial_update(self, request):

    def get(self, request):
        """Show request"""
        user = request.user
        return Response({ 'user.id': user.id, 'user.email': user.email, 'user.first_name': user.first_name, 'user.last_name': user.last_name})

class TutorView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        """Index request"""
        tutors = User.objects.filter(is_tutor=True)
        # Run the data through the serializer
        serializer = TutorSerializer(tutors, many=True).data
        print('serializer', serializer)
        return Response({'tutors': serializer})
