# Import necessary modules from Django and Django Rest Framework
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from django.db.models import Count
from .schema import server_list_docs

# Import all models from the current app
from . models import *

# Import the ServerSerializer from the serializer module
from . serializer import ServerSerializer

# Define the ServerListViewSet class, which inherits from viewsets.ViewSet
class ServerListViewSet(viewsets.ViewSet):
    # Define the queryset attribute, which is a QuerySet of all Server objects
    queryset = Server.objects.all()

    # Define the list method, which handles GET requests to the viewset
    @server_list_docs
    def list(self, request):
        # Get the category, qty, by_user, by_serverid, and with_num_members parameters from the request query params
        category = request.query_params.get("category")
        qty = request.query_params.get("qty")
        by_user = request.query_params.get("by_user") == "true"
        by_serverid = request.query_params.get("by_serverid")
        with_num_members = request.query_params.get("with_num_members") == "true"

        # Filter the queryset by category if the category parameter is provided
        if category:
            self.queryset = self.queryset.filter(category=category)

        # Limit the queryset to the specified quantity if the qty parameter is provided
        if qty:
            self.queryset = self.queryset[: int(qty)]

        # Check if the user is authenticated if the by_user or by_serverid parameters are provided
        # if by_user or by_serverid and not request.user.is_authenticated:
        #     raise AuthenticationFailed()

        # Filter the queryset by the current user's ID if the by_user parameter is provided
        if by_user:
            user_id = request.user.id
            self.queryset = self.queryset.filter(member=user_id)
        else:
            raise AuthenticationFailed()

        # Annotate the queryset with the number of members if the with_num_members parameter is provided
        if with_num_members:
            self.queryset = self.queryset.annotate(num_members=Count("member"))

        # Filter the queryset by the specified server ID if the by_serverid parameter is provided
        if by_serverid:
            try:
                self.queryset = self.queryset.filter(id=by_serverid)
                # Raise a ValidationError if the server with the specified ID is not found
                if not self.queryset.exists():
                    raise ValidationError(detail=f"Server With Id {by_serverid} Is Not Found!")
            except ValueError:
                # Raise a ValidationError if the server ID is invalid
                raise ValidationError(detail=f"Server Value Error!")

        # Serialize the queryset using the ServerSerializer
        serializer = ServerSerializer(self.queryset, many=True, context={"nummbers": with_num_members})
        # Return a Response object with the serialized data
        return Response(serializer.data)